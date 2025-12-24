import json
import os

folder_path = os.getcwd()

total_count = 0

for filename in os.listdir(folder_path):
    if filename.endswith(".json"):
        file_path = os.path.join(folder_path, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        count = len(data)
        total_count += count
        print(f"{filename}: {count} ")


