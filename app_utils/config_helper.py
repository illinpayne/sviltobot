# config_helper.py

import os
import json
from app_utils.config import (
    USERS_FILE,
    DATA_DIR,
    AVAILABLE_AREA_CODES,
    logger
) # Імпортуємо константи з config.py


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


# --- ФУНКЦІЇ РОБОТИ З КОРИСТУВАЧАМИ (ПОКИ ЗАЛИШАЄМО ТУТ) ---

def load_users():
    """Завантажує дані користувачів із файлу."""
    if not os.path.exists(USERS_FILE):
        # Перевірка та створення файлу, якщо його немає
        try:
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump({}, f)
        except Exception as e:
            logger.error(f"Не вдалося створити {USERS_FILE}: {e}")
            return {}

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