import json
import config
from utils import load_json, save_json, load_prompt, query_llm

def run():
    print("--- Step 3: Mask Generation ---")
    
    prompts = {
        "DIRECT": load_prompt("direct_mask_construction.txt"),
        "DOUBLE": load_prompt("isare_double_mask_construction.txt"),
        "SOFT": load_prompt("isare_soft_mask_construction.txt")
    }

    # Iterate through files in the mask directory (generated in step 2)
    # Note: Your original code looked for ALL files in MASKDIR, but MASKDIR now contains FINAL_*.json
    # We should only process files that need masking.
    
    files = list(config.MASK_DIR.glob("FINAL*"))
    for file in files:
        # Determine prompt type based on filename
        mask_prompt = ""
        for p_key, p_text in prompts.items():
            if p_key in file.name:
                mask_prompt = p_text
        
        if not mask_prompt:
            # Fallback or skip if no matching prompt type (e.g., WH questions might need specific logic)
            continue

        user_input = load_json(file)
        
        # Call LLM
        print(f"Generating masks for {file.name}...")
        response_str = query_llm(mask_prompt, str(user_input))
        
        try:
            response_json = json.loads(response_str)
            save_json(response_json, config.MASK_DIR / f"MASK_{file.name}")
        except json.JSONDecodeError:
            print(f"Failed to decode mask JSON for {file.name}")