# parser/storage/json_writer.py
# storage/json_writer.py
import json

def save_to_json(data, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
