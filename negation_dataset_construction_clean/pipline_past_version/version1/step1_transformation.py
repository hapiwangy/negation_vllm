import json
import config
from utils import load_json, save_json, load_prompt, query_llm
import os

def run():
    print("--- Step 1: Negation Transformation ---")
    
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

    # Process Yes/No Questions
    for x in range(ITER):
        batch_data = yesno_content[NUM * x : NUM * (x + 1)]
        for key, prompt_text in prompts["ISARE"].items():
            print(f"Processing ISARE batch {x+1}, type {key}...")
            response_str = query_llm(prompt_text, str(batch_data))
            try:
                response_json = json.loads(response_str)
                filename = f"ISARE_{key}{NUM * x}{NUM * (x + 1)}.json"
                save_json(response_json, config.ISARE_DIR / filename)
            except json.JSONDecodeError:
                print(f"Failed to decode JSON for batch {x}")

    # Process WH Questions
    for x in range(ITER):
        batch_data = wh_content[NUM * x : NUM * (x + 1)]
        for key, prompt_text in prompts["WH"].items():
            print(f"Processing WH batch {x+1}, type {key}...")
            response_str = query_llm(prompt_text, str(batch_data))
            try:
                response_json = json.loads(response_str)
                filename = f"WH_{key}{NUM * x}{NUM * (x + 1)}.json"
                save_json(response_json, config.WH_DIR / filename)
            except json.JSONDecodeError:
                print(f"Failed to decode JSON for batch {x}")