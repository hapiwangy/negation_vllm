import config
from utils import load_json, save_json

def run():
    answer_cal = {"a":0, "b":0}
    print("--- Step 2: Answer Construction ---")
    failed_files = []
    # 1. Process ISARE files
    isare_files = list(config.ISARE_DIR.glob("ISARE*"))
    for file in isare_files:
        try:
            data = load_json(file)
        except Exception as e:
            failed_files.append(file)
            print(f"Failed to load {file}: {e}")
            continue
        result = []
        for element in data:            
            if answer_cal["a"] < answer_cal["b"]: 
                answer_cal["a"] += 1
                correct_answer = "a" if element['neg_a'] == "yes" else "b"
                options = {"a": "yes", "b": "no"}
            else:
                answer_cal["b"] += 1
                correct_answer = "b" if element['neg_a'] == "yes" else "a"
                options = {"a": "no", "b": "yes"}    
            new_element = {
                "id": element['id'],
                "q": element['q'],
                "a": element['a'],
                "neg_q": element['neg_q'],
                "options": options,
                'ca': correct_answer
            }
            result.append(new_element)
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
        
        try:
            whneg = load_json(wf)
        except Exception as e:
            failed_files.append(wf)
            print(f"Failed to load {wf}: {e}")
            continue
        try:
            whanswer = load_json(answer_file)
        except Exception as e:
            failed_files.append(answer_file)
            print(f"Failed to load {answer_file}: {e}")
            continue        
        # Create lookup dict
        whanswer_map = {x['neg_q']: x for x in whanswer if 'neg_q' in x}

        result = []
        for element in whneg:
            if element.get('neg_q') == "not_applicable":
                continue
            

            if element['q'] in whanswer_map: 
                pass
            ans_entry = next((item for item in whanswer if item["q"] == element["q"]), None)
            
            if ans_entry:
                if answer_cal["a"] < answer_cal["b"]: 
                    answer_cal["a"] += 1
                    # since the new answer is also b, so that we reverse the options
                    correct_answer = "a" 
                    options = {"a": ans_entry["options"]["b"], "b": ans_entry["options"]["a"]}
                else:
                    answer_cal["b"] += 1
                    correct_answer = "b" 
                    options = ans_entry["options"]

                new_element = {
                    "id": str(element['id']),
                    "q": element["q"],
                    "a": element["a"],
                    "neg_q": element["neg_q"],
                    "options": options,
                    "ca": correct_answer
                } 
                result.append(new_element)

        save_json(result, config.MASK_DIR / f"FINAL_{wf.name}")
    print(answer_cal)