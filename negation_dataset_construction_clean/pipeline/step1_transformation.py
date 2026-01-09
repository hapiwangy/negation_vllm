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

def run():
    print("--- Step 1: Negation Transformation (Multithread) ---")

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

    NUM = int(os.getenv("TASK1NUM"))
    ITER = int(os.getenv("TASK1ITER"))
    START = int(os.getenv("TASK1START"))

    tasks = []

    #  thread pool
    #  change based on the api limitation
    with ThreadPoolExecutor(max_workers=2) as executor:

        # ISARE
        for x in range(ITER):
            FROM = START + NUM * x
            UNTIL = START + NUM * (x + 1)
            if STOP_EVENT.is_set(): break
            batch_data = yesno_content[FROM : UNTIL]
            for key, prompt_text in prompts["ISARE"].items():
                if STOP_EVENT.is_set(): break
                filename = f"ISARE_{key}{FROM}{UNTIL}.json"
                save_path = config.ISARE_DIR / filename
                # desc = (x + 1, key)
                desc = f"ISARE batch {x+1}, type {key}"

                future = executor.submit(
                    process_batch,
                    prompt_text,
                    batch_data,
                    save_path,
                    desc
                )
                tasks.append(future)

        # WH
        for x in range(ITER):
            FROM = START + NUM * x
            UNTIL = START + NUM * (x + 1)
            if STOP_EVENT.is_set(): break
            batch_data = wh_content[FROM : UNTIL]
            for key, prompt_text in prompts["WH"].items():
                if STOP_EVENT.is_set(): break
                filename = f"WH_{key}{FROM}{UNTIL}.json"
                save_path = config.WH_DIR / filename
                desc = f"WH batch {x+1}, type {key}"

                future = executor.submit(
                    process_batch,
                    prompt_text,
                    batch_data,
                    save_path,
                    desc
                )
                tasks.append(future)

        # wait for the thread to be finished
        for future in as_completed(tasks):
            future.result()

    print("=== All tasks completed ===")
