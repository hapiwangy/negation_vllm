import json
import config
from utils import load_json, save_json, load_prompt, query_llm
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Event 
STOP_EVENT = Event()

def process_batch(prompt_text, batch_data, save_path, desc):
    if STOP_EVENT.is_set(): return
    print(f"Processing {desc}...")
    try:
        response_str = query_llm(prompt_text, str(batch_data))
        try:
            response_json = json.loads(response_str)
            save_json(response_json, save_path)
            print(f"Saved {save_path.name}")
        except json.JSONDecodeError:
            print(f"Failed to decode JSON for {desc}")
            # save the org content to the txt files for future parsing
            with open(save_path, "w+", encoding="utf-8") as fp:
                fp.write(response_str)
    except Exception as e:
        STOP_EVENT.set()
        progress = {
            "desc": desc,
            "save_path": str(save_path),
            "batch_size": len(batch_data),
            "error_type": type(e).__name__,
            "error_message": str(e),
        }

        with open("errorhappened.json", "w", encoding="utf-8") as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)

def process_batch_return(prompt_text, batch_data, desc):
    """Run LLM on batch_data and return parsed JSON (or raw string if JSON fails)."""
    if STOP_EVENT.is_set():
        return None
    print(f"Processing {desc}...")
    try:
        response_str = query_llm(prompt_text, str(batch_data))
        try:
            return json.loads(response_str)
        except json.JSONDecodeError:
            print(f"Failed to decode JSON for {desc}")
            return response_str
    except Exception as e:
        STOP_EVENT.set()
        progress = {
            "desc": desc,
            "batch_size": len(batch_data),
            "error_type": type(e).__name__,
            "error_message": str(e),
        }
        with open("errorhappened.json", "w", encoding="utf-8") as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
        raise

def run():
    print("--- Step 1: Negation Transformation (2-thread: ISARE + WH) ---")

    # Load Prompts
    prompts = {
        "ISARE": {
            "DIRECT": load_prompt("isare_direct_negation.txt"),
            "DOUBLE": load_prompt("isare_double_negation.txt"),
            "SOFT": load_prompt("isare_soft_negation.txt")
        },
        "WH": {
            "DIRECT": load_prompt("wh_direct_negation.txt"),
            "ADDING": load_prompt("wh_adding_answers.txt")
        }
    }

    # Load Data
    yesno_content = load_json(config.DATASET_DIR / "yesno_content.json")
    wh_content = load_json(config.DATASET_DIR / "wh_content.json")

    # Shared controls
    NUM = int(os.getenv("TASK1NUM"))
    ITER = int(os.getenv("TASK1ITER"))

    # Split starts (one group for ISARE, one group for WH)
    ISARESTART = int(os.getenv("TASK1ISARESTART"))
    WHSTART = int(os.getenv("TASK1WHSTART"))

    # ISARE total volume = 3x WH.
    # Implementation detail to ensure EACH LLM call receives NUM items:
    # For each WH-sized "block" (b), we take a span of 3*NUM items and split into
    # three NUM-sized batches by picking every 3rd item.
    ISARE_BLOCKS = ITER  # number of 3*NUM spans
    ISARE_CYCLE = ["DIRECT", "SOFT", "DOUBLE"]  # mapping for offsets 0/1/2

    def isare_worker():
        for b in range(ISARE_BLOCKS):
            BASE_FROM = ISARESTART + (3 * NUM) * b
            BASE_UNTIL = ISARESTART + (3 * NUM) * (b + 1)

            if STOP_EVENT.is_set():
                break

            span = yesno_content[BASE_FROM:BASE_UNTIL]  # length = 3*NUM

            # Build three NUM-sized batches:
            # DIRECT: span[0], span[3], ...
            # SOFT:   span[1], span[4], ...
            # DOUBLE: span[2], span[5], ...
            for offset, key in enumerate(ISARE_CYCLE):
                if STOP_EVENT.is_set():
                    break

                batch_items = span[offset::3]  # should be NUM items
                prompt_text = prompts["ISARE"][key]
                desc = f"ISARE block {b+1}/{ISARE_BLOCKS}, type {key}, batch_size={len(batch_items)}"

                result = process_batch_return(prompt_text, batch_items, desc)

                filename = f"ISARE_{key}{BASE_FROM}{BASE_UNTIL}.json"
                save_path = config.ISARE_DIR / filename

                payload = {
                    "from": BASE_FROM,
                    "until": BASE_UNTIL,
                    "transform": key,
                    "stride_offset": offset,   # 0/1/2 within the 3*NUM span
                    "stride": 3,
                    "data": result,
                }
                save_json(payload["data"], save_path)
                print(f"[ISARE] Saved {save_path.name}")

    def wh_worker():
        for x in range(ITER):
            FROM = WHSTART + NUM * x
            UNTIL = WHSTART + NUM * (x + 1)
            if STOP_EVENT.is_set():
                break

            batch_data = wh_content[FROM:UNTIL]
            for key, prompt_text in prompts["WH"].items():
                if STOP_EVENT.is_set():
                    break

                filename = f"WH_{key}{FROM}{UNTIL}.json"
                save_path = config.WH_DIR / filename
                desc = f"WH batch {x+1}, type {key}"

                process_batch(prompt_text, batch_data, save_path, desc)
                print(f"[WH] Saved {save_path.name}")

    # Run ISARE and WH in two separate threads
    with ThreadPoolExecutor(max_workers=4) as executor:
        f_isare = executor.submit(isare_worker)
        f_wh = executor.submit(wh_worker)
        f_isare.result()
        f_wh.result()

    print("=== All tasks completed ===")
