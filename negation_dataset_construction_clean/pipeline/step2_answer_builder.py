import config
from utils import load_json, save_json
import os


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return str(v).strip().lower() in {"1", "true", "yes", "y", "on"}


def run():
    answer_cal = {"a": 0, "b": 0}
    print("--- Step 2: Answer Construction (Respect doisare/dowh) ---")

    DO_ISARE = _env_bool("DOISARE", default=False)
    DO_WH = _env_bool("DOWH", default=False)

    if not DO_ISARE and not DO_WH:
        print("[Step2] Both doisare=0 and dowh=0, nothing to do.")
        return

    failed_files = []

    # 1. Process ISARE files
    if DO_ISARE:
        isare_files = list(config.ISARE_DIR.glob("ISARE*"))
        for file in isare_files:
            try:
                data = load_json(file)
            except Exception as e:
                failed_files.append(file)
                print(f"Failed to load {file}: {e}")
                continue

            # sometime output "Invalid", which will cause the error
            if not isinstance(data, list):
                continue

            result = []
            for element in data:
                if answer_cal["a"] < answer_cal["b"]:
                    answer_cal["a"] += 1
                    correct_answer = "a" if element["neg_a"] == "yes" else "b"
                    options = {"a": "yes", "b": "no"}
                else:
                    answer_cal["b"] += 1
                    correct_answer = "b" if element["neg_a"] == "yes" else "a"
                    options = {"a": "no", "b": "yes"}

                new_element = {
                    "id": element["id"],
                    "q": element["q"],
                    "a": element["a"],
                    "neg_q": element["neg_q"],
                    "options": options,
                    "ca": correct_answer,
                }
                result.append(new_element)

            save_json(result, config.MASK_DIR / f"FINAL_{file.name}")

        print("[Step2][ISARE] Done")
    else:
        print("[Step2][ISARE] Skipped (doisare=0)")

    # 2. Process WH files
    if DO_WH:
        wh_files = list(config.WH_DIR.glob("WH_DIRECT*"))
        error_logs = []  # 記錄 item/檔案錯誤，不讓流程中斷

        for wf in wh_files:
            suffix = wf.name.replace("WH_DIRECT", "")
            answer_file = config.WH_DIR / f"WH_ADDING{suffix}"

            if not answer_file.exists():
                msg = f"Warning: Answer file {answer_file} not found for {wf}"
                print(msg)
                error_logs.append({"level": "file", "file": wf.name, "reason": "answer_file_missing", "detail": msg})
                continue

            # 檔案層：讀取失敗 -> 記錄後直接下一個檔案
            try:
                whneg = load_json(wf)
            except Exception as e:
                msg = f"Failed to load {wf}: {e}"
                print(msg)
                failed_files.append(wf)
                error_logs.append({"level": "file", "file": wf.name, "reason": "whneg_load_failed", "error": str(e)})
                continue

            try:
                whanswer = load_json(answer_file)
            except Exception as e:
                msg = f"Failed to load {answer_file}: {e}"
                print(msg)
                failed_files.append(answer_file)
                error_logs.append(
                    {"level": "file", "file": answer_file.name, "reason": "whanswer_load_failed", "error": str(e)}
                )
                continue

            # 建立 q -> answer 的索引
            ans_by_q = {}
            for idx, item in enumerate(whanswer):
                qv = item.get("q") if isinstance(item, dict) else None
                if qv is None:
                    error_logs.append(
                        {
                            "level": "item",
                            "file": answer_file.name,
                            "reason": "missing_q_in_whanswer_item",
                            "index": idx,
                            "item_preview": item if isinstance(item, dict) else str(item),
                        }
                    )
                    continue
                ans_by_q[qv] = item

            result = []
            for element in whneg:
                try:
                    if not isinstance(element, dict):
                        continue

                    if element.get("neg_q") == "not_applicable":
                        continue

                    q = element.get("q")
                    if q is None:
                        error_logs.append(
                            {"level": "item", "file": wf.name, "reason": "missing_q_in_whneg_element", "id": element.get("id")}
                        )
                        continue

                    ans_entry = ans_by_q.get(q)
                    if not ans_entry:
                        error_logs.append(
                            {"level": "item", "file": wf.name, "reason": "answer_not_found_for_q", "id": element.get("id"), "q": q}
                        )
                        continue

                    options_src = ans_entry.get("options")
                    if not isinstance(options_src, dict) or "a" not in options_src or "b" not in options_src:
                        error_logs.append(
                            {"level": "item", "file": answer_file.name, "reason": "invalid_options_in_answer", "q": q, "options": options_src}
                        )
                        continue

                    if answer_cal["a"] < answer_cal["b"]:
                        answer_cal["a"] += 1
                        correct_answer = "a"
                        options = {"a": options_src["b"], "b": options_src["a"]}
                    else:
                        answer_cal["b"] += 1
                        correct_answer = "b"
                        options = options_src

                    new_element = {
                        "id": str(element.get("id")),
                        "q": q,
                        "a": element.get("a"),
                        "neg_q": element.get("neg_q"),
                        "options": options,
                        "ca": correct_answer,
                    }
                    result.append(new_element)

                except Exception as e:
                    error_logs.append(
                        {"level": "item", "file": wf.name, "reason": "exception_in_processing_element", "id": element.get("id"), "error": str(e)}
                    )
                    continue

            save_json(result, config.MASK_DIR / f"FINAL_{wf.name}")

        if error_logs:
            save_json(error_logs, config.MASK_DIR / "step2_answer_builder_error_log.json")
            print(f"[Step2] Error log saved: {config.MASK_DIR / 'step2_answer_builder_error_log.json'}")

        print("[Step2][WH] Done")
    else:
        print("[Step2][WH] Skipped (dowh=0)")

    print("=== Step2 completed ===")
