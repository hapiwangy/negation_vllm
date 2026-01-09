import json
from openai import OpenAI
import config

client = OpenAI(api_key=config.OPENAI_API_KEY)

def load_json(path):
    with open(path, "r", encoding="utf-8") as fp:
        return json.load(fp)

def save_json(data, path):
    with open(path, "w+", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=4)

def load_prompt(filename):
    with open(config.PROMPT_DIR / filename, "r", encoding="utf-8") as fp:
        return fp.read()

def query_llm(system_prompt, user_input):
    try:
        response = client.responses.create(
            model=config.MODEL_ID,
            input =[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_input}
            ]
        )
        return response.output_text
    except Exception as e:
        print(f"Error querying LLM: {e}")
        return "{}" # Return empty json string on error or handle appropriately
