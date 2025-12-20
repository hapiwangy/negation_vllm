import config
from utils import load_json, save_json

def mask_produce(numdict):
    # Logic extracted from original
    if len(numdict) == 3:
        return [0] * (numdict['A'] + numdict['B']) + [1] * (numdict['C']) + [0]
    else:
        return [0] * (numdict['A'] + numdict['B']) + [1] * (numdict['C']) + [0] * (numdict['D']) + [1] * (numdict['E']) + [0]

def run():
    print("--- Step 4: Final Dataset Compilation ---")
    
    files = list(config.MASK_DIR.glob("FINAL*"))
    for file in files:
        mask_filename = config.MASK_DIR / f"MASK_{file.name}"
        
        if not mask_filename.exists():
            continue

        mask_data = load_json(mask_filename)
        org_data = load_json(file)

        # Create lookup map
        mask_map = {m['neg_q']: m for m in mask_data}

        for s in org_data:
            if s['neg_q'] in mask_map:
                dims = mask_map[s['neg_q']]['part_lengths']
                s['mask'] = mask_produce(dims)
            else:
                s['mask'] = [] # Handle missing masks

        save_json(org_data, config.FINAL_SET_DIR / file.name)