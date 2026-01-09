import json
import config
from utils import load_json, save_json, load_prompt, query_llm
from concurrent.futures import ThreadPoolExecutor, as_completed


def process_file(file_path, prompts):
    # Determine prompt type based on filename
    mask_prompt = ""
    for p_key, p_text in prompts.items():
        if p_key in file_path.name:
            mask_prompt = p_text
            break

    if not mask_prompt:
        print(f"Skip {file_path.name}: no matching prompt key in filename.")
        return

    user_input = load_json(file_path)

    print(f"Generating masks for {file_path.name}...")
    response_str = query_llm(mask_prompt, str(user_input))

    try:
        response_json = json.loads(response_str)
        out_path = config.MASK_DIR / f"MASK_{file_path.name}"
        save_json(response_json, out_path)
        print(f"Saved {out_path.name}")
    except json.JSONDecodeError:
        print(f"Failed to decode mask JSON for {file_path.name}")


def run():
    print("--- Step 3: Mask Generation (Multithread) ---")

    prompts = {
        "DIRECT": load_prompt("direct_mask_construction.txt"),
        "DOUBLE": load_prompt("isare_double_mask_construction.txt"),
        "SOFT": load_prompt("isare_soft_mask_construction.txt"),
    }

    files = list(config.MASK_DIR.glob("FINAL*"))


    max_workers = 4

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_file, f, prompts) for f in files]
        for fut in as_completed(futures):
            fut.result()

    print("=== Step 3 completed ===")
