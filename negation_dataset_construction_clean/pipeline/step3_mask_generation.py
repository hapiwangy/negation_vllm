import json
import config
from utils import load_json, save_json, load_prompt, query_llm
from concurrent.futures import ThreadPoolExecutor, as_completed


def process_file(file_path, prompts):
    """處理單一 FINAL*.json 檔案：選 prompt → 呼叫 LLM → 存 MASK_*.json"""
    # Determine prompt type based on filename
    mask_prompt = ""
    for p_key, p_text in prompts.items():
        if p_key in file_path.name:
            mask_prompt = p_text
            break

    if not mask_prompt:
        # 沒匹配到就跳過（例如 WH 或其他命名規則）
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

    # 只處理 FINAL*（照你註解的想法）
    files = list(config.MASK_DIR.glob("FINAL*"))

    # 可依 API rate limit 調整
    max_workers = 8

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_file, f, prompts) for f in files]
        for fut in as_completed(futures):
            # 把 thread 裡的例外拋出來，避免悄悄失敗
            fut.result()

    print("=== Step 3 completed ===")
