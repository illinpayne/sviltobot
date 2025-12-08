import json
import os


def save_to_json(data, save_path: str):
    """
    Зберігає або оновлює дані в JSON файлі.
    Якщо файл існує, додає нову дату до існуючих даних.
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    existing_data = {}
    if os.path.exists(save_path):
        try:
            with open(save_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            existing_data = {}

    existing_data.update(data)

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)