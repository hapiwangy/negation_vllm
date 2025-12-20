import json
import os
CUR_PATH = os.getcwd()
TASK = "negation_dataset_construction"
DATASET = "org_dataset"
DEST = "dataset"

def trans_into_dict(input:str):
    # input is a json dictionary, leave only image_id, question, answer
    input = list(input)
    new_input = []
    for i in input:
        new_input.append({
            "image_id": i['image_id'],
            "question": i['question'],
            "answer": i['answer']
        })
    return new_input
# read the yesno questions
with open(os.path.join(CUR_PATH, TASK, DATASET, "vqa_yesno.json"), "r", encoding="utf-8") as fp:
    yesno_content = json.loads(fp.read())
# read the 5w questions
with open(os.path.join(CUR_PATH, TASK, DATASET, "vqa_other.json"), "r", encoding="utf-8") as fp:
    wh_content = json.loads(fp.read())

# clean the input
yesno_content = trans_into_dict(yesno_content)
wh_content = trans_into_dict(wh_content)
yesno_content = [x for x in yesno_content if x['answer'] == "yes" or x['answer'] == "no"]
wh_content = [x for x in wh_content if x['answer'] != "yes" and x['answer'] != "no"]
WH_WORDS = ("what", "who", "which", "when", "where", "why", "how")
def is_wh_or_how(question: str) -> bool:
    return question.strip().lower().startswith(WH_WORDS)
wh_content = [d for d in wh_content if is_wh_or_how(d["question"])]

# store to the destination 
with open(os.path.join(CUR_PATH, TASK, DEST, "yesno_content.json"), "w+", encoding="utf-8") as f:
    json.dump(yesno_content, f, ensure_ascii=False, indent=4)
with open(os.path.join(CUR_PATH, TASK, DEST, "wh_content.json"), "w+", encoding="utf-8") as f:
    json.dump(wh_content, f, ensure_ascii=False, indent=4)

# here can log that the dataset contribution is successful