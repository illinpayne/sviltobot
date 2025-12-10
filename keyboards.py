from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

DONATION_LINK = "https://send.monobank.ua/jar/YOUR_DONATION_JAR_ID"


# ГОЛОВНЕ МЕНЮ

def main_menu_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("👤 Профіль"))
    kb.add(KeyboardButton("⚡ Графік світла"))
    kb.add(KeyboardButton("❓ Допомога"))
    return kb


#  ПРОФІЛЬ

def profile_keyboard(prof: dict):
    """
    Кнопки профілю:
      • Змінити місто
      • Додати/редагувати черги
      • Сповіщення про оновлення
      • Нагадування (5/15/30 хв)
    """
    kb = InlineKeyboardMarkup()

    notif = "✅ Увімкнено" if prof.get("notifications_enabled") else "❌ Вимкнено"

    offsets = prof.get("reminder_offsets", [])
    if offsets:
        sorted_offsets = sorted(set(int(o) for o in offsets))
        rem_text = ", ".join(f"{o} хв" for o in sorted_offsets)
    else:
        rem_text = "вимкнені"

    kb.add(InlineKeyboardButton("🌍 Змінити місто", callback_data="profile_change_city"))
    kb.add(InlineKeyboardButton("➕ Додати/редагувати черги", callback_data="profile_edit"))
    kb.add(InlineKeyboardButton(f"🔔 Оновлення графіку: {notif}", callback_data="profile_toggle_notif"))
    kb.add(InlineKeyboardButton(f"⏰ Нагадування: {rem_text}", callback_data="profile_reminders"))

    return kb


# ВИБІР ЧЕРГ

def queues_keyboard(selected: list, all_queues: list):
    kb = InlineKeyboardMarkup(row_width=3)

    for q in all_queues:
        checked = "✅" if q in selected else "⬜"
        cb = f"queue_toggle_{q}"
        kb.add(InlineKeyboardButton(f"{checked} {q}", callback_data=cb))

    kb.add(InlineKeyboardButton("⬅ Назад", callback_data="back_profile"))
    return kb


# ВИБІР МІСТА

def city_select_keyboard(cities, current_city: str):
    """
    cities: список кортежів (code, title)
    """
    kb = InlineKeyboardMarkup(row_width=1)

    for code, title in cities:
        checked = "✅" if code == current_city else "⬜"
        cb = f"city_set_{code}"
        kb.add(InlineKeyboardButton(f"{checked} {title}", callback_data=cb))

    kb.add(InlineKeyboardButton("⬅ Назад до профілю", callback_data="back_profile"))
    return kb


# НАЛАШТУВАННЯ НАГАДУВАНЬ

def reminders_keyboard(active_offsets: list):
    """
    active_offsets – список хвилин, для яких увімкнені нагадування (5/15/30).
    """
    kb = InlineKeyboardMarkup(row_width=3)
    active_set = set(int(o) for o in active_offsets)

    for off in (5, 15, 30):
        checked = "✅" if off in active_set else "⬜"
        cb = f"rem_offset_{off}"
        kb.add(InlineKeyboardButton(f"{checked} {off} хв", callback_data=cb))

    kb.add(InlineKeyboardButton("⬅ Назад до профілю", callback_data="back_profile"))
    return kb


# НАВІГАЦІЯ ГРАФІКУ

def schedule_navigation_keyboard(current_mode: str, show_all_queues: bool):
    """
    Кнопки:
    • Сьогодні / Завтра
    • Мої черги / Всі черги
    """
    kb = InlineKeyboardMarkup()

    scope = "all" if show_all_queues else "my"

    # Перемикач today <-> tomorrow
    if current_mode == "today":
        kb.add(
            InlineKeyboardButton(
                "📆 Графік на завтра",
                callback_data=f"nav_tomorrow_{scope}",
            )
        )
    else:
        kb.add(
            InlineKeyboardButton(
                "📅 Графік на сьогодні",
                callback_data=f"nav_today_{scope}",
            )
        )

    # Перемикач мої/всі
    if show_all_queues:
        kb.add(
            InlineKeyboardButton(
                "📊 Показати лише мої черги",
                callback_data=f"nav_{current_mode}_my",
            )
        )
    else:
        kb.add(
            InlineKeyboardButton(
                "🌍 Показати всі черги міста",
                callback_data=f"nav_{current_mode}_all",
            )
        )

    return kb


# ВИБІР НАГАДУВАННЯ (запас)

def reminder_selection_keyboard(city: str, selected_queues: list, outage_finder):
    """
    Зараз не використовується в main.py, але залишаємо як helper на майбутнє.
    """
    kb = InlineKeyboardMarkup(row_width=1)
    all_events = []

    for q in selected_queues:
        next_outages = outage_finder(city, q, count=2)

        for dt in next_outages:
            text = f"{q} • {dt.strftime('%d.%m %H:%M')}"
            cb = f"rem_select_{q}_{dt.strftime('%Y%m%dT%H%M')}"
            kb.add(InlineKeyboardButton(text, callback_data=cb))
            all_events.append((q, dt))

    kb.add(InlineKeyboardButton("⬅ Назад до профілю", callback_data="back_profile"))
    return kb, all_events


# ДОПОМОГА / ДОНАТ

def help_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("💸 Підтримати розробника", url=DONATION_LINK))
    kb.add(InlineKeyboardButton("⬅ Назад", callback_data="menu_back"))
    return kb
