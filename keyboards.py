# keyboards.py
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, KeyboardButton, InlineKeyboardButton
from config import REGIONS, get_area_title, list_available_areas


# --- REPLY КЛАВІАТУРИ ---

def main_menu_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        KeyboardButton("⚡ Графік світла"),
        KeyboardButton("👤 Мій профіль"),
        KeyboardButton("❓ Допомога / Донат"),
    )
    return kb


# --- INLINE КЛАВІАТУРИ ---

def profile_keyboard(prof):
    kb = InlineKeyboardMarkup(row_width=1)

    # Кнопка Область
    kb.add(InlineKeyboardButton(text="🌍 Змінити область", callback_data="profile_change_area"))

    # Кнопка Черги
    kb.add(InlineKeyboardButton(text="📟 Змінити черги", callback_data="profile_edit"))

    # Кнопка Нагадування
    kb.add(InlineKeyboardButton(text="⏰ Нагадування", callback_data="profile_reminders"))

    # Кнопка Сповіщення
    notif_text = "🔕 Вимкнути сповіщення про оновлення" if prof.get(
        "notifications_enabled") else "🔔 Увімкнути сповіщення про оновлення"
    kb.add(InlineKeyboardButton(text=notif_text, callback_data="profile_toggle_notif"))

    # Додано кнопку для повернення до меню
    kb.add(InlineKeyboardButton(text="🏠 Головне меню", callback_data="menu_back"))

    return kb


def queues_keyboard(selected_queues: list, all_queues: list):
    kb = InlineKeyboardMarkup(row_width=3)
    buttons = []

    for q in all_queues:
        text = f"✅ {q}" if q in selected_queues else q
        buttons.append(InlineKeyboardButton(text=text, callback_data=f"queue_toggle_{q}"))

    kb.add(*buttons)
    kb.add(InlineKeyboardButton(text="⬅️ Назад до профілю", callback_data="back_profile"))
    return kb


def schedule_navigation_keyboard(current_mode: str, showing_all: bool):
    kb = InlineKeyboardMarkup(row_width=2)

    # Навігація за датою
    today_btn = InlineKeyboardButton(
        text="Сьогодні" if current_mode != "today" else "▶️ Сьогодні",
        callback_data=f"nav_today_{'all' if showing_all else 'my'}",
    )
    tomorrow_btn = InlineKeyboardButton(
        text="Завтра" if current_mode != "tomorrow" else "▶️ Завтра",
        callback_data=f"nav_tomorrow_{'all' if showing_all else 'my'}",
    )
    kb.add(today_btn, tomorrow_btn)

    # Перемикач "Мої черги" / "Всі черги"
    scope_text = "🌍 Показати всі черги" if not showing_all else "📟 Показати мої черги"
    scope_data = f"nav_{current_mode}_{'all' if not showing_all else 'my'}"
    kb.add(InlineKeyboardButton(text=scope_text, callback_data=scope_data))

    kb.add(InlineKeyboardButton(text="🏠 Головне меню", callback_data="menu_back"))
    return kb


def reminders_keyboard(selected_offsets: list):
    kb = InlineKeyboardMarkup(row_width=3)
    available_offsets = [5, 10, 15, 30, 60]  # хвилини

    buttons = []
    for offset in available_offsets:
        text = f"✅ {offset} хв" if offset in selected_offsets else f"{offset} хв"
        buttons.append(InlineKeyboardButton(text=text, callback_data=f"rem_offset_{offset}"))

    kb.add(*buttons)
    kb.add(InlineKeyboardButton(text="⬅️ Назад до профілю", callback_data="back_profile"))
    return kb


def help_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(text="💳 Підтримати розробників", url="https://send.monobank.ua/jar/A9ur6kxT1r"))
    kb.add(InlineKeyboardButton(text="🏠 Головне меню", callback_data="menu_back"))
    return kb


# --- КЛАВІАТУРИ ДЛЯ ВИБОРУ ОБЛАСТІ ---

def region_select_keyboard():
    """Клавіатура для вибору регіону (Захід, Північ, Південь, Схід)."""
    kb = InlineKeyboardMarkup()
    available_codes = set(list_available_areas())

    for region_code, region_data in REGIONS.items():
        # Додаємо регіони лише якщо в них є доступні області
        has_available_area = any(code in available_codes for code in region_data["areas"].keys())
        if has_available_area:
            btn = InlineKeyboardButton(
                text=region_data["title"],
                callback_data=f"region_select_{region_code}",
            )
            kb.add(btn)

    kb.add(InlineKeyboardButton(text="⬅️ Назад до профілю", callback_data="back_profile"))
    return kb


def area_select_keyboard(region_code: str, current_area_code: str):
    """Клавіатура для вибору області в межах вибраного регіону."""
    kb = InlineKeyboardMarkup(row_width=2)

    region_data = REGIONS.get(region_code)
    if not region_data:
        return kb

    available_codes = set(list_available_areas())

    buttons = []
    for code, title in region_data["areas"].items():
        if code in available_codes:
            title_text = f"✅ {title}" if code == current_area_code else title
            buttons.append(InlineKeyboardButton(
                text=title_text,
                callback_data=f"area_set_{code}",
            ))

    kb.add(*buttons)

    kb.add(InlineKeyboardButton(text="⬅️ Назад до регіонів", callback_data="back_regions"))
    return kb