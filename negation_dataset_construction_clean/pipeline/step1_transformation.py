import json
import config
from utils import load_json, save_json, load_prompt, query_llm
import os
from concurrent.futures import ThreadPoolExecutor, as_completed


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return str(v).strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    v = os.getenv(name)
    if v is None:
        return 0
    try:
        return int(str(v).strip())
    except Exception:
        return default


def _log_error(desc: str, save_path: str | None, batch_size: int, e: Exception):
    progress = {
        "desc": desc,
        "save_path": save_path,
        "batch_size": batch_size,
        "error_type": type(e).__name__,
        "error_message": str(e),
    }
    # 覆寫最後一次錯誤（如果你想保留多筆，可改成 append log）
    with open("errorhappened.json", "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def process_batch(prompt_text, batch_data, save_path, desc):
    print(f"Processing {desc}...")
    try:
        response_str = query_llm(prompt_text, str(batch_data))
        try:
            response_json = json.loads(response_str)
            save_json(response_json, save_path)
            print(f"Saved {save_path.name}")
        except json.JSONDecodeError:
            print(f"Failed to decode JSON for {desc}")
            # save raw content for future parsing
            with open(save_path, "w+", encoding="utf-8") as fp:
                fp.write(response_str)
    except Exception as e:
        _log_error(desc=desc, save_path=str(save_path), batch_size=len(batch_data), e=e)
        # 不再 stop 全局；這個 batch 失敗就算了，讓其他任務繼續


def run_isare(prompts, yesno_content, NUM, ITER, ISARESTART, isare_max_workers: int):
    print(f"[Step1][ISARE] max_workers={isare_max_workers}")

    ISARE_BLOCKS = ITER
    ISARE_CYCLE = ["DIRECT", "SOFT", "DOUBLE"]  # offset 0/1/2

    tasks = []
    with ThreadPoolExecutor(max_workers=isare_max_workers) as executor:
        for b in range(ISARE_BLOCKS):
            BASE_FROM = ISARESTART + (3 * NUM) * b
            BASE_UNTIL = ISARESTART + (3 * NUM) * (b + 1)

            span = yesno_content[BASE_FROM:BASE_UNTIL]  # length should be 3*NUM

            for offset, key in enumerate(ISARE_CYCLE):
                batch_items = span[offset::3]  # should be NUM items
                prompt_text = prompts["ISARE"][key]
                desc = f"ISARE block {b+1}/{ISARE_BLOCKS}, type {key}, batch_size={len(batch_items)}"

                filename = f"ISARE_{key}{BASE_FROM}{BASE_UNTIL}.json"
                save_path = config.ISARE_DIR / filename

                tasks.append(executor.submit(process_batch, prompt_text, batch_items, save_path, desc))

        # 等全部完成（同時把例外吃掉，避免中途中斷）
        for fut in as_completed(tasks):
            try:
                fut.result()
            except Exception as e:
                # process_batch 本身已寫 errorhappened.json，這裡只做保險
                _log_error(desc="[ISARE] unexpected future exception", save_path=None, batch_size=0, e=e)

    print("[Step1][ISARE] Done")


def run_wh(prompts, wh_content, NUM, ITER, WHSTART, wh_max_workers: int):
    print(f"[Step1][WH] max_workers={wh_max_workers}")

    tasks = []
    with ThreadPoolExecutor(max_workers=wh_max_workers) as executor:
        for x in range(ITER):
            FROM = WHSTART + NUM * x
            UNTIL = WHSTART + NUM * (x + 1)

            batch_data = wh_content[FROM:UNTIL]
            for key, prompt_text in prompts["WH"].items():
                filename = f"WH_{key}{FROM}{UNTIL}.json"
                save_path = config.WH_DIR / filename
                desc = f"WH batch {x+1}/{ITER}, type {key}, batch_size={len(batch_data)}"

                tasks.append(executor.submit(process_batch, prompt_text, batch_data, save_path, desc))

        for fut in as_completed(tasks):
            try:
                fut.result()
            except Exception as e:
                _log_error(desc="[WH] unexpected future exception", save_path=None, batch_size=0, e=e)

    print("[Step1][WH] Done")


def run():
    print("--- Step 1: Negation Transformation (Independent ISARE/WH pipelines) ---")

    # 開關：控制要不要跑 ISARE / WH
    DO_ISARE = _env_bool("DOISARE", default=False)
    DO_WH = _env_bool("DOWH", default=False)

    if not DO_ISARE and not DO_WH:
        print("[Step1] Both doisare=0 and dowh=0, nothing to do.")
        return

    # Load Prompts
    prompts = {
        "ISARE": {
            "DIRECT": load_prompt("isare_direct_negation.txt"),
            "DOUBLE": load_prompt("isare_double_negation.txt"),
            "SOFT": load_prompt("isare_soft_negation.txt"),
        },
        "WH": {
            "DIRECT": load_prompt("wh_direct_negation.txt"),
            "ADDING": load_prompt("wh_adding_answers.txt"),
        },
    }

    # Shared controls
    NUM = _env_int("TASK1NUM", default=0)
    ITER = _env_int("TASK1ITER", default=0)
    ISARESTART = _env_int("TASK1ISARESTART", default=0)
    WHSTART = _env_int("TASK1WHSTART", default=0)

    # Independent max_workers
    ISARE_MAX_WORKERS = 4
    WH_MAX_WORKERS = 4

    # Load Data (only load what we need)
    yesno_content = None
    wh_content = None

    if DO_ISARE:
        yesno_content = load_json(config.DATASET_DIR / "yesno_content.json")

    if DO_WH:
        wh_content = load_json(config.DATASET_DIR / "wh_content.json")

    # 若兩個都要跑：外層用 2 thread 同時啟動兩條獨立 pipeline
    if DO_ISARE and DO_WH:
        with ThreadPoolExecutor(max_workers=2) as outer:
            f1 = outer.submit(run_isare, prompts, yesno_content, NUM, ITER, ISARESTART, ISARE_MAX_WORKERS)
            f2 = outer.submit(run_wh, prompts, wh_content, NUM, ITER, WHSTART, WH_MAX_WORKERS)
            f1.result()
            f2.result()
    elif DO_ISARE:
        run_isare(prompts, yesno_content, NUM, ITER, ISARESTART, ISARE_MAX_WORKERS)
    elif DO_WH:
        run_wh(prompts, wh_content, NUM, ITER, WHSTART, WH_MAX_WORKERS)
    else:
        print("Running nothing in this run")
    print("=== Step1 completed ===")
