# schedule_helper.py

import os
import json
from datetime import datetime
from app_utils.config import DATA_DIR, logger # Імпортуємо константи та логер з config.py
from app_utils.config_helper import get_area_title # Імпортуємо функцію для назви області


# --- ФУНКЦІЇ РОБОТИ З ГРАФІКАМИ ---

def load_area_schedule(area_code: str):
    """Завантажує графік області із JSON-файлу."""
    path = os.path.join(DATA_DIR, f"{area_code}.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Помилка завантаження графіку {area_code}: {e}")
        return {}


def get_schedule_hash(area_code: str):
    """Хеш для визначення змін у файлі."""
    data = load_area_schedule(area_code)
    # Використовуємо dumps з sort_keys=True для стабільного хешу
    return hash(json.dumps(data, sort_keys=True))


def get_sorted_dates(data: dict):
    """Сортує дати у форматі dd.mm.yyyy."""
    try:
        return sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d.%m.%Y"))
    except Exception:
        # Якщо парсинг дати не вдався, повертаємо несортований список ключів
        return list(data.keys())


def choose_date(data: dict, mode: str):
    """
    mode: "today" / "tomorrow"
    Повертає ключ дати з JSON.
    """
    if not data:
        return None

    dates = get_sorted_dates(data)
    if not dates:
        return None

    if mode == "today":
        return dates[0]
    elif mode == "tomorrow":
        return dates[1] if len(dates) > 1 else None
    return dates[0]


def all_area_queues(area_code: str):
    """Витягуємо список черг із JSON (перша доступна дата) для області."""
    data = load_area_schedule(area_code)
    if not data:
        return []
    dates = get_sorted_dates(data)
    if not dates:
        return []
    first_date = dates[0]
    return sorted(list(data.get(first_date, {}).keys()))


def get_outage_intervals_for_queue(area_code: str, queue: str):
    """Повертає всі інтервали відключень для СЬОГОДНІ та ЗАВТРА (якщо є)."""
    data = load_area_schedule(area_code)
    if not data:
        return []

    intervals = []
    sorted_dates = get_sorted_dates(data)

    for date_str in sorted_dates[:2]:  # today + tomorrow (якщо є)
        try:
            date_obj = datetime.strptime(date_str, "%d.%m.%Y")
        except Exception:
            continue

        for interval in data.get(date_str, {}).get(queue, []):
            try:
                start_raw, end_raw = interval.split(" - ")
                # Припускаємо формат H-M, але перевірка часу потрібна, якщо дані чисті
                start_dt_time = datetime.strptime(start_raw, "%H-%M")
                end_dt_time = datetime.strptime(end_raw, "%H-%M")

                start_dt = date_obj.replace(
                    hour=start_dt_time.hour, minute=start_dt_time.minute, second=0, microsecond=0,
                )
                end_dt = date_obj.replace(
                    hour=end_dt_time.hour, minute=end_dt_time.minute, second=0, microsecond=0,
                )

                intervals.append((start_dt, end_dt))
            except Exception as e:
                logger.error(f"Помилка парсингу інтервалу: {interval} для {date_str}. {e}")
                continue

    return intervals


def build_schedule_message(queues, area_code, mode, title_prefix=""):
    """Генерує текстове повідомлення з графіком відключень."""
    data = load_area_schedule(area_code)
    area_title = get_area_title(area_code)

    if not data:
        return "❌ Графік ще не опубліковано. Перевірте пізніше."

    date_key = choose_date(data, mode)
    date_label = "Сьогодні" if mode == "today" else "Завтра"

    # Спеціальна обробка для "Завтра"
    if mode == "tomorrow" and (not date_key or date_key not in data):
        return (
            f"{title_prefix}<b>Графік відключень</b>\n"
            f" Область: <b>{area_title}</b>\n"
            f" Завтра — <b>очікується оновлення даних</b>.\n\n"
            f"Дані з’являться, щойно їх опублікує Обленерго."
        )

    if not date_key or date_key not in data:
        return (
            f"{title_prefix}<b>Графік відключень</b>\n"
            f" Область: <b>{area_title}</b>\n"
            f" {date_label} — <b>очікується оновлення даних</b>."
        )

    day_data = data.get(date_key, {})
    formatted_blocks = []

    for q in queues:
        intervals = day_data.get(q, [])

        if not intervals:
            formatted_blocks.append(f"<b>Черга {q}</b>\n   –")
        else:
            interval_lines = "\n".join(f"   • {i}" for i in intervals)
            formatted_blocks.append(f"<b>Черга {q}</b>\n{interval_lines}")

    # Перевірка, чи всі черги мають "–" (тобто немає відключень)
    if all("–" in block for block in formatted_blocks):
        return (
            f"{title_prefix}<b>Графік відключень</b>\n"
            f" Область: <b>{area_title}</b>\n"
            f" {date_label} ({date_key})\n\n"
            f"У вибраних черг <b>немає відключень</b> на цей день."
        )

    header = (
        f"{title_prefix}<b>Графік відключень</b>\n"
        f" Область: <b>{area_title}</b>\n"
        f" {date_label} ({date_key})\n\n"
    )

    return header + "\n\n".join(formatted_blocks)
