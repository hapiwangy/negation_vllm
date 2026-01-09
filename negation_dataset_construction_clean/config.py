import os
from pathlib import Path
from dotenv import load_dotenv


load_dotenv()


BASE_DIR = Path(os.getcwd())
# TASK_DIR = BASE_DIR / "negation_dataset_construction"
TASK_DIR = BASE_DIR 
PROMPT_DIR = TASK_DIR / "prompts"
DATASET_DIR = TASK_DIR / "dataset"


RESULT_DIR = TASK_DIR / "NegQResult"
ISARE_DIR = RESULT_DIR / "Negisare"
WH_DIR = RESULT_DIR / "Negwh"
MASK_DIR = RESULT_DIR / "NegQMask"
FINAL_SET_DIR = TASK_DIR / "Cleaneddata"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_ID = "gpt-5-mini" 


for path in [ISARE_DIR, WH_DIR, MASK_DIR, FINAL_SET_DIR]:
    path.mkdir(parents=True, exist_ok=True)