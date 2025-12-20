import os
from pathlib import Path
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數
load_dotenv()

# 基本路徑設定
BASE_DIR = Path(os.getcwd())
# TASK_DIR = BASE_DIR / "negation_dataset_construction"
TASK_DIR = BASE_DIR 
PROMPT_DIR = TASK_DIR / "prompts"
DATASET_DIR = TASK_DIR / "dataset"

# 輸出目錄結構
RESULT_DIR = TASK_DIR / "NegQResult"
ISARE_DIR = RESULT_DIR / "Negisare"
WH_DIR = RESULT_DIR / "Negwh"
MASK_DIR = RESULT_DIR / "NegQMask"
FINAL_SET_DIR = TASK_DIR / "Cleaneddata"

# 模型設定
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_ID = "gpt-5-mini" # 建議使用標準模型名稱，或保持你的 "gpt-5-mini"

# 確保所有輸出目錄存在
for path in [ISARE_DIR, WH_DIR, MASK_DIR, FINAL_SET_DIR]:
    path.mkdir(parents=True, exist_ok=True)