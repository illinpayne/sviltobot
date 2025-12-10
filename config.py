# config.py

import os
import json
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# --- НАЛАШТУВАННЯ ТА ІНІЦІАЛІЗАЦІЯ ---

load_dotenv()
TOKEN = os.getenv("API_KEY")

if not TOKEN:
    # Залишаємо виняток тут, бо це критична помилка конфігурації
    raise ValueError("❌ API_KEY не знайдено у .env файлі!")

USERS_FILE = "users.json"
DATA_DIR = "parser/data"

# Нова структура: РЕГІОНИ -> ОБЛАСТІ -> КОД (назва файлу)
REGIONS = {
    "west": {
        "title": "Західний 🇺🇦",
        "areas": {
            "lviv": "Львівська",
            "ivano-frankivsk": "Івано-Франківська",
            "ternopil": "Тернопільська",
            "volyn": "Волинська",
            "rivne": "Рівненська",
            "zakarpattia": "Закарпатська",
            "chernivtsi": "Чернівецька",
            "khmelnytskyi": "Хмельницька",
        }
    },
    "north": {
        "title": "Північний та Центр 🌻",
        "areas": {
            "kyivcity": "Київ (Місто)",
            "kyivobl": "Київська (Область)",
            "zhytomyr": "Житомирська",
            "vinnytsia": "Вінницька",
            "chernihiv": "Чернігівська",
            "sumy": "Сумська",
            "cherkasy": "Черкаська",
            "kirovohrad": "Кіровоградська",
            "poltava": "Полтавська",
        }
    },
    "south": {
        "title": "Південний 🌊",
        "areas": {
            "odesa": "Одеська",
            "mykolaiv": "Миколаївська",
            "kherson": "Херсонська",  # Додано для повноти, навіть якщо графіки можуть бути недоступні
            "zaporizhzhia": "Запорізька",
        }
    },
    "east": {
        "title": "Східний 🛡️",
        "areas": {
            "dnipro": "Дніпропетровська",
            "kharkiv": "Харківська",
            "donetsk": "Донецька",  # Додано для повноти
            "luhansk": "Луганська",  # Додано для повноти
        }
    }
}

# Плоский список усіх кодів областей
AVAILABLE_AREA_CODES = {code: title for region in REGIONS.values() for code, title in region['areas'].items()}

CHECK_INTERVAL_SEC = 300  # Раз на 5 хвилин

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- ГЛОБАЛЬНІ СТРУКТУРИ ДАНИХ (для воркера) ---
SENT_REMINDERS_LOG = {}
LAST_SCHEDULE_HASH = {}


# --- ДОПОМІЖНІ ФУНКЦІЇ ДЛЯ КОНФІГУРАЦІЇ ---

def list_available_areas():
    """Сканує папку DATA_DIR та повертає список кодів областей, для яких є JSON-файл."""
    if not os.path.exists(DATA_DIR):
        return []

    available = []
    for code in AVAILABLE_AREA_CODES.keys():
        filename = f"{code}.json"
        if os.path.exists(os.path.join(DATA_DIR, filename)):
            available.append(code)

    return available


def get_area_title(area_code: str) -> str:
    """Отримує назву області для відображення."""
    return AVAILABLE_AREA_CODES.get(area_code, area_code.capitalize())


def get_default_area() -> str:
    """Отримує область за замовчуванням (перша доступна або 'rivne')."""
    areas = list_available_areas()
    return areas[0] if areas else "rivne"


# --- ФУНКЦІЇ РОБОТИ З КОРИСТУВАЧАМИ ---

def load_users():
    """Завантажує дані користувачів із файлу."""
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)

    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Помилка завантаження {USERS_FILE}: {e}")
        return {}


def save_users(data: dict):
    """Зберігає дані користувачів у файл."""
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Помилка збереження {USERS_FILE}: {e}")


def save_user_profile(uid: int, profile: dict):
    """Зберігає профіль одного користувача."""
    users = load_users()
    users[str(uid)] = profile
    save_users(users)


def get_user_profile(uid: int):
    """
    Завантажує профіль користувача, створює новий, якщо не знайдено,
    і виконує міграцію/перевірку даних.
    """
    users = load_users()
    uid_str = str(uid)

    if uid_str not in users:
        # Створення нового профілю
        users[uid_str] = {
            "area": get_default_area(),
            "queues": [],
            "notifications_enabled": False,
            "reminder_offsets": [],
        }
        save_users(users)

    prof = users[uid_str]
    should_save = False

    # Міграція старого поля 'city' на 'area'
    if "city" in prof:
        prof["area"] = prof.pop("city")
        should_save = True

    # Міграція старих полів reminder_offsets
    if "reminder_offsets" not in prof:
        offsets = []
        if "reminder_offset" in prof and prof["reminder_offset"]:
            try:
                val = int(prof["reminder_offset"])
                if val > 0:
                    offsets = [val]
            except Exception:
                offsets = []
        prof["reminder_offsets"] = offsets
        if "reminder_offset" in prof:
            prof.pop("reminder_offset", None)
        should_save = True

    if "notifications_enabled" not in prof:
        prof["notifications_enabled"] = False
        should_save = True

    # Перевірка області
    available = list_available_areas()
    if available:
        if prof.get("area") not in available:
            prof["area"] = available[0]
            prof["queues"] = []
            should_save = True
    else:
        # Якщо немає жодного файла-області, ставимо fallback
        if "area" not in prof:
            prof["area"] = "rivne"
            should_save = True

    if should_save:
        save_user_profile(uid, prof)

    return prof


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
    return hash(json.dumps(data, sort_keys=True))


def get_sorted_dates(data: dict):
    """Сортує дати у форматі dd.mm.yyyy."""
    try:
        return sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d.%m.%Y"))
    except Exception:
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
                start_dt_time = datetime.strptime(start_raw, "%H-%M")
                end_dt_time = datetime.strptime(end_raw, "%H-%M")

                start_dt = date_obj.replace(
                    hour=start_dt_time.hour,
                    minute=start_dt_time.minute,
                    second=0,
                    microsecond=0,
                )
                end_dt = date_obj.replace(
                    hour=end_dt_time.hour,
                    minute=end_dt_time.minute,
                    second=0,
                    microsecond=0,
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