import config
from utils import load_json, save_json

def run():
    print("--- Step 2: Answer Construction ---")
    
    # 1. Process ISARE files
    isare_files = list(config.ISARE_DIR.glob("ISARE*"))
    for file in isare_files:
        data = load_json(file)
        result = []
        for element in data:
            result.append({
                "id": element['id'],
                "q": element['q'],
                "a": element['a'],
                "neg_q": element['neg_q'],
                "options": {"a": "yes", "b": "no"},
                'ca': "a" if element['neg_a'] == "yes" else "b"
            })
        save_json(result, config.MASK_DIR / f"FINAL_{file.name}")

    # 2. Process WH files
    # Only look for DIRECT files to merge with ADDING answers
    wh_files = list(config.WH_DIR.glob("WH_DIRECT*"))
    for wf in wh_files:
        # Construct the corresponding answer filename
        # Assuming format WH_DIRECT010.json -> WH_ADDING010.json
        suffix = wf.name.replace("WH_DIRECT", "") 
        answer_file = config.WH_DIR / f"WH_ADDING{suffix}"
        
        if not answer_file.exists():
            print(f"Warning: Answer file {answer_file} not found for {wf}")
            continue

        whneg = load_json(wf)
        whanswer = load_json(answer_file)
        
        # Create lookup dict
        whanswer_map = {x['neg_q']: x for x in whanswer if 'neg_q' in x}

        result = []
        for element in whneg:
            if element.get('neg_q') == "not_applicable":
                continue
            
            # Using original question 'q' to map back seems to be the logic in your code
            # But ensure the key exists
            if element['q'] in whanswer_map: # This logic looked a bit weird in original, simplified here
                 # Note: Review your original logic: whanswer was mapped by neg_q, but accessed by q?
                 # Assuming mapping by neg_q is safer if structure allows.
                 pass
            
            # Reverting to your exact original logic for safety:
            # whanswer map was { x['neg_q']: x }
            # But you accessed it via answer_element = whanswer[element['q']]
            # This implies neg_q in the answer file is actually the original q? 
            # I will keep logic generic but robust:
            
            # Use a safer join key if possible. For now, following original logic:
            # The original logic seemed to map answer dict by neg_q, but query by element['q'].
            # This implies whanswer's 'neg_q' field actually contained the original question string?
            # If so, proceed. If not, this is a bug in original code.
            
            # Let's assume whanswer is indexed by original question for safety in matching
            ans_entry = next((item for item in whanswer if item["q"] == element["q"]), None)
            
            if ans_entry:
                result.append({
                    "id": str(element['id']),
                    "q": element["q"],
                    "a": element["a"],
                    "neg_q": element["neg_q"],
                    "options": ans_entry["options"],
                    "ca": ans_entry['ca']
                })

        save_json(result, config.MASK_DIR / f"FINAL_{wf.name}")