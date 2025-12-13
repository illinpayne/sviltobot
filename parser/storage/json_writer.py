import json
import os
from datetime import datetime


def save_to_json(data, save_path: str):

    # Зберігає або оновлює дані в JSON файлі.
    # Якщо файл існує, додає нову сьогоднішню або майбутню відому дату до існуючих даних

    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    existing_data = {}
    if os.path.exists(save_path):
        try:
            with open(save_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            existing_data = {}


    today = datetime.now().date()

    filtered_data = {}
    for date_str, queues in existing_data.items():
        try:
            date_obj = datetime.strptime(date_str, "%d.%m.%Y").date()
            if date_obj >= today:
                filtered_data[date_str] = queues
        except ValueError:
            continue

    filtered_data.update(data)

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(filtered_data, f, ensure_ascii=False, indent=2)