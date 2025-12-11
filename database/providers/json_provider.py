import json
import os


class JSONProvider:
    def __init__(self, directory_path: str = "data"):
        self.directory_path = directory_path

        os.makedirs(self.directory_path, exist_ok=True)

    def save(self, filename: str, data):
        if not filename.endswith(".json"):
            filename = filename + ".json"

        file_path = os.path.join(self.directory_path, filename)

        with open(file_path, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def load(self, filename: str) -> dict:
        if not filename.endswith(".json"):
            filename = filename + ".json"

        file_path = os.path.join(self.directory_path, filename)

        if os.path.exists(file_path):
            with open(file_path, "r", encoding='utf-8') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {}
        else:
            return {}
