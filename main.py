import os
import json
import logging
import time
from datetime import datetime, timedelta
from threading import Timer

from telebot import TeleBot
from dotenv import load_dotenv
import telebot
telebot.logger.setLevel(logging.DEBUG)

from keyboards import (
    main_menu_keyboard,
    profile_keyboard,
    queues_keyboard,
    schedule_navigation_keyboard,
    reminder_selection_keyboard,  # на майбутнє
    help_keyboard,
    city_select_keyboard,
    reminders_keyboard,
)

# НАЛАШТУВАННЯ

load_dotenv()
TOKEN = os.getenv("API_KEY")

if not TOKEN:
    raise ValueError("❌ API_KEY не знайдено у .env файлі!")

bot = TeleBot(TOKEN)

USERS_FILE = "users.json"
DATA_DIR = "parser/data"

# назви міст (інші будуть city.capitalize())
CITY_TITLES = {
    "rivne": "Рівне",
}

CHECK_INTERVAL_SEC = 300  # Раз на 5 хвилин

logging.basicConfig(level=logging.INFO)

SENT_REMINDERS_LOG = {}  # { "20251210": { "user_id": ["20251210T1530_5", ...] } }
LAST_SCHEDULE_HASH = {}  # { "rivne": 123456, "kyiv": 654321 }
global_timer = None


# ДОПОМІЖНІ ФУНКЦІЇ

def list_available_cities():
    """Сканує папку DATA_DIR та повертає список кодів міст (без .json)."""
    if not os.path.exists(DATA_DIR):
        return []

    cities = []
    for name in os.listdir(DATA_DIR):
        if name.lower().endswith(".json"):
            code = os.path.splitext(name)[0]
            cities.append(code.lower())
    return sorted(set(cities))


def get_city_title(city_code: str) -> str:
    return CITY_TITLES.get(city_code, city_code.capitalize())


def get_default_city() -> str:
    cities = list_available_cities()
    if cities:
        return cities[0]
    return "rivne"


# КОРИСТУВАЧІ

def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)

    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_users(data: dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_user_profile(uid: int, profile: dict):
    users = load_users()
    users[str(uid)] = profile
    save_users(users)


def get_user_profile(uid: int):
    users = load_users()
    uid_str = str(uid)

    if uid_str not in users:
        users[uid_str] = {
            "city": get_default_city(),
            "queues": [],
            "notifications_enabled": False,
            "reminder_offsets": [],  # [5, 15, 30]
        }
        save_users(users)

    prof = users[uid_str]

    # Міграція старих полів
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
        save_user_profile(uid, prof)

    if "notifications_enabled" not in prof:
        prof["notifications_enabled"] = False
        save_user_profile(uid, prof)

    # Перевірка міста
    available = list_available_cities()
    if available:
        if prof.get("city") not in available:
            prof["city"] = available[0]
            prof["queues"] = []
            save_user_profile(uid, prof)
    else:
        # Якщо немає жодного файла–міста, підставляємо 'rivne'
        if "city" not in prof:
            prof["city"] = "rivne"
            save_user_profile(uid, prof)

    return prof


# JSON ФАЙЛ ГРАФІКІВ

def load_city_schedule(city: str):
    path = os.path.join(DATA_DIR, f"{city}.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def get_schedule_hash(city: str):
    """Хеш для визначення змін у файлі."""
    data = load_city_schedule(city)
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


def all_city_queues(city: str):
    """
    Витягуємо список черг із JSON (перша доступна дата).
    """
    data = load_city_schedule(city)
    if not data:
        return []
    dates = get_sorted_dates(data)
    if not dates:
        return []
    first_date = dates[0]
    return sorted(list(data.get(first_date, {}).keys()))


# ІНТЕРВАЛИ ВІДКЛЮЧЕНЬ

def get_outage_intervals_for_queue(city: str, queue: str):
    """
    Повертає всі інтервали відключень (start_dt, end_dt)
    для СЬОГОДНІ та ЗАВТРА (якщо є).
    """
    data = load_city_schedule(city)
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
            except Exception:
                continue

    return intervals


# СПОВІЩЕННЯ ПРО ЗМІНИ

def send_schedule_change_notification(chat_id, city):
    msg = (
        f"🚨 <b>Графік оновлено!</b>\n"
        f"Місто: <b>{get_city_title(city)}</b>\n\n"
        f"Перевірте меню <b>⚡ Графік світла</b>."
    )
    bot.send_message(chat_id, msg, parse_mode="html")


# ГЕНЕРАЦІЯ ТЕКСТУ ГРАФІКА

def build_schedule_message(queues, city, mode, title_prefix=""):
    data = load_city_schedule(city)

    # Якщо немає даних взагалі
    if not data:
        return "❌ Графік ще не опубліковано. Перевірте пізніше."

    date_key = choose_date(data, mode)

    # Якщо просимо "завтра", а другої дати ще немає
    if mode == "tomorrow" and (not date_key or date_key not in data):
        return (
            f"{title_prefix}<b>Графік відключень</b>\n"
            f" Місто: <b>{get_city_title(city)}</b>\n"
            f" Завтра — <b>очікується оновлення даних</b>.\n\n"
            f"Дані з’являться, щойно їх опублікує Обленерго."
        )

    if not date_key or date_key not in data:
        date_label = "Сьогодні" if mode == "today" else "Завтра"
        return (
            f"{title_prefix}<b>Графік відключень</b>\n"
            f" Місто: <b>{get_city_title(city)}</b>\n"
            f" {date_label} — <b>очікується оновлення даних</b>."
        )

    day_data = data.get(date_key, {})
    date_label = "Сьогодні" if mode == "today" else "Завтра"

    formatted_blocks = []

    for q in queues:
        intervals = day_data.get(q, [])

        if not intervals:
            formatted_blocks.append(
                f"<b>Черга {q}</b>\n"
                f"   –"
            )
        else:
            interval_lines = "\n".join(f"   • {i}" for i in intervals)
            formatted_blocks.append(
                f"<b>Черга {q}</b>\n"
                f"{interval_lines}"
            )

    # якщо у всіх черг "–"
    if all("–" in block for block in formatted_blocks):
        return (
            f"{title_prefix}<b>Графік відключень</b>\n"
            f" Місто: <b>{get_city_title(city)}</b>\n"
            f" {date_label} ({date_key})\n\n"
            f"У вибраних черг <b>немає відключень</b> на цей день."
        )

    header = (
        f"{title_prefix}<b>Графік відключень</b>\n"
        f" Місто: <b>{get_city_title(city)}</b>\n"
        f" {date_label} ({date_key})\n\n"
    )

    return header + "\n\n".join(formatted_blocks)


def send_schedules_list(chat_id, queues, city, mode, title_prefix="", message_id=None, show_all_queues=False):
    text = build_schedule_message(queues, city, mode, title_prefix)
    kb = schedule_navigation_keyboard(mode, show_all_queues)

    if message_id:
        bot.edit_message_text(text, chat_id, message_id, parse_mode="html", reply_markup=kb)
    else:
        bot.send_message(chat_id, text, parse_mode="html", reply_markup=kb)


# ФОНОВИЙ ВОРКЕР

def check_and_send_all_alerts():
    global global_timer, LAST_SCHEDULE_HASH

    global_timer = Timer(CHECK_INTERVAL_SEC, check_and_send_all_alerts)
    global_timer.daemon = False
    global_timer.start()

    try:
        now = datetime.now()
        users = load_users()

        # Перевірка змін графіка по всіх містах
        cities = list_available_cities()
        for city in cities:
            schedule_hash = get_schedule_hash(city)

            if city not in LAST_SCHEDULE_HASH:
                LAST_SCHEDULE_HASH[city] = schedule_hash
            elif schedule_hash != LAST_SCHEDULE_HASH[city]:
                logging.warning(f"Зміна графіка для {city}!")
                for uid_str, profile in users.items():
                    if profile.get("city") == city and profile.get("notifications_enabled"):
                        send_schedule_change_notification(int(uid_str), city)
                LAST_SCHEDULE_HASH[city] = schedule_hash

        # Перевірка нагадувань

        reminder_window_start = now
        reminder_window_end = now + timedelta(seconds=CHECK_INTERVAL_SEC)

        today_key = now.strftime("%Y%m%d")
        if today_key not in SENT_REMINDERS_LOG:
            SENT_REMINDERS_LOG[today_key] = {}

        for uid_str, profile in users.items():
            uid = int(uid_str)
            offsets = profile.get("reminder_offsets", [])
            if not offsets:
                continue

            user_city = profile.get("city", get_default_city())
            queues = profile.get("queues", [])

            for queue in queues:
                intervals = get_outage_intervals_for_queue(user_city, queue)

                for start_dt, _ in intervals:
                    for offset in offsets:
                        try:
                            offset_int = int(offset)
                        except Exception:
                            continue
                        if offset_int <= 0:
                            continue

                        reminder_dt = start_dt - timedelta(minutes=offset_int)
                        reminder_id = f"{start_dt.strftime('%Y%m%dT%H%M')}_{offset_int}"

                        if not (reminder_window_start <= reminder_dt <= reminder_window_end):
                            continue

                        sent_for_user = SENT_REMINDERS_LOG[today_key].get(uid_str, [])
                        if reminder_id in sent_for_user:
                            continue

                        msg = (
                            f"💡 <b>СКОРО ВІДКЛЮЧЕННЯ</b>\n"
                            f"Місто: <b>{get_city_title(user_city)}</b>\n"
                            f"Черга <b>{queue}</b>\n"
                            f"Початок о <b>{start_dt.strftime('%H:%M')}</b>\n"
                            f"Нагадування за <b>{offset_int} хв</b>."
                        )
                        try:
                            bot.send_message(uid, msg, parse_mode="html")
                            SENT_REMINDERS_LOG[today_key].setdefault(uid_str, []).append(reminder_id)
                            logging.info(f"Надіслано нагадування користувачу {uid} для черги {queue}, offset={offset_int}")
                        except Exception as e:
                            logging.error(f"Не вдалося надіслати нагадування {uid}: {e}")

        logging.info("Воркер завершив перевірку.")

    except Exception as e:
        logging.error(f"Помилка у воркері: {e}")


# ХЕНДЛЕРИ БОТА

@bot.message_handler(commands=["start"])
def cmd_start(m):
    text = (
        "Привіт! Я СвітлоБот ⚡\n\n"
        "Я допоможу дізнатися, коли у твоєму районі буде світло чи темрява.\n"
        "Для початку роботи скористайся кнопками внизу 👇"
    )
    bot.send_message(m.chat.id, text, reply_markup=main_menu_keyboard())


# ПРОФІЛЬ
@bot.message_handler(func=lambda m: m.text and "проф" in m.text.lower())
def profile_msg(m):
    prof = get_user_profile(m.from_user.id)
    queues = ", ".join(prof["queues"]) if prof["queues"] else "не вибрані"

    text = (
        f"👤 <b>Ваш профіль</b>\n\n"
        f"ID: <code>{m.from_user.id}</code>\n"
        f"Місто: <b>{get_city_title(prof['city'])}</b>\n"
        f"📟 Черги: {queues}"
    )

    bot.send_message(
        m.chat.id,
        text,
        parse_mode="html",
        reply_markup=profile_keyboard(prof),
    )

@bot.callback_query_handler(func=lambda c: c.data == "profile_edit")
def edit_queues(call):
    prof = get_user_profile(call.from_user.id)

    city = prof["city"]
    all_q = all_city_queues(city)  # ← ПРАВИЛЬНО

    kb = queues_keyboard(prof["queues"], all_q)

    bot.edit_message_text(
        "Оберіть ваші черги:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=kb
    )
# @bot.callback_query_handler(func=lambda c: c.data == "profile_edit")
# def edit_queues(call):
#     prof = get_user_profile(call.from_user.id)
#     all_q = all_city_queues(prof["city"])
#     if not all_q:
#         bot.answer_callback_query(call.id, "Немає даних про черги для цього міста.")
#         return
#
#     kb = queues_keyboard(prof["queues"], all_q)
#
#     bot.edit_message_text(
#         "Оберіть ваші черги:",
#         call.message.chat.id,
#         call.message.message_id,
#         reply_markup=kb,
#     )
#     bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("queue_toggle_"))
def queue_toggle(call):
    prof = get_user_profile(call.from_user.id)
    all_q = all_city_queues(prof["city"])

    q = call.data.split("_", 2)[-1]
    if q not in all_q:
        bot.answer_callback_query(call.id, "Невідома черга.")
        return

    if q in prof["queues"]:
        prof["queues"].remove(q)
    else:
        prof["queues"].append(q)

    prof["queues"].sort()
    save_user_profile(call.from_user.id, prof)

    kb = queues_keyboard(prof["queues"], all_q)
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=kb)
    bot.answer_callback_query(call.id, "Збережено!")


@bot.callback_query_handler(func=lambda c: c.data == "back_profile")
def back_profile(call):
    prof = get_user_profile(call.from_user.id)
    queues = ", ".join(prof["queues"]) if prof["queues"] else "не вибрані"

    text = (
        f"👤 <b>Ваш профіль</b>\n\n"
        f"ID: <code>{call.from_user.id}</code>\n"
        f"Місто: <b>{get_city_title(prof['city'])}</b>\n"
        f"📟 Черги: {queues}"
    )

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="html",
        reply_markup=profile_keyboard(prof),
    )
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == "profile_toggle_notif")
def toggle_notifications(call):
    prof = get_user_profile(call.from_user.id)
    prof["notifications_enabled"] = not prof.get("notifications_enabled", False)
    save_user_profile(call.from_user.id, prof)

    queues = ", ".join(prof["queues"]) if prof["queues"] else "не вибрані"
    text = (
        f"👤 <b>Ваш профіль</b>\n\n"
        f"ID: <code>{call.from_user.id}</code>\n"
        f"Місто: <b>{get_city_title(prof['city'])}</b>\n"
        f"📟 Черги: {queues}"
    )

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="html",
        reply_markup=profile_keyboard(prof),
    )

    status = "увімкнено" if prof["notifications_enabled"] else "вимкнено"
    bot.answer_callback_query(call.id, f"Сповіщення про оновлення: {status}")


@bot.callback_query_handler(func=lambda c: c.data == "profile_change_city")
def profile_change_city(call):
    prof = get_user_profile(call.from_user.id)
    cities_codes = list_available_cities()
    if not cities_codes:
        bot.answer_callback_query(call.id, "Немає доступних міст (немає файлів у parser/data).")
        return

    cities = [(code, get_city_title(code)) for code in cities_codes]
    kb = city_select_keyboard(cities, prof["city"])

    bot.edit_message_text(
        "🌍 Оберіть місто:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=kb,
    )
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("city_set_"))
def set_city(call):
    city = call.data.split("_", 2)[-1]
    available = list_available_cities()
    if city not in available:
        bot.answer_callback_query(call.id, "Місто більше недоступне.")
        return

    prof = get_user_profile(call.from_user.id)
    prof["city"] = city
    # при зміні міста скидаємо черги
    prof["queues"] = []
    save_user_profile(call.from_user.id, prof)

    queues = "не вибрані"
    text = (
        f"👤 <b>Ваш профіль</b>\n\n"
        f"ID: <code>{call.from_user.id}</code>\n"
        f"Місто: <b>{get_city_title(prof['city'])}</b>\n"
        f"📟 Черги: {queues}"
    )

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="html",
        reply_markup=profile_keyboard(prof),
    )

    bot.answer_callback_query(call.id, f"Місто змінено на {get_city_title(city)}")


@bot.callback_query_handler(func=lambda c: c.data == "profile_reminders")
def open_reminders(call):
    prof = get_user_profile(call.from_user.id)
    kb = reminders_keyboard(prof.get("reminder_offsets", []))

    bot.edit_message_text(
        "⏰ Налаштування нагадувань.\n\nУвімкніть потрібні інтервали:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="html",
        reply_markup=kb,
    )
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("rem_offset_"))
def toggle_reminder_offset(call):
    try:
        offset = int(call.data.split("_")[-1])
    except Exception:
        bot.answer_callback_query(call.id, "Помилка значення.")
        return

    prof = get_user_profile(call.from_user.id)
    offsets = set(int(o) for o in prof.get("reminder_offsets", []))

    if offset in offsets:
        offsets.remove(offset)
    else:
        offsets.add(offset)

    prof["reminder_offsets"] = sorted(offsets)
    save_user_profile(call.from_user.id, prof)

    kb = reminders_keyboard(prof["reminder_offsets"])

    bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        reply_markup=kb,
    )

    if offset in offsets:
        msg = f"Нагадування за {offset} хв увімкнено."
    else:
        msg = f"Нагадування за {offset} хв вимкнено."

    bot.answer_callback_query(call.id, msg)


# ГРАФІК СВІТЛА

@bot.message_handler(func=lambda m: m.text and "графік" in m.text.lower())
def graph_default_show(m):
    prof = get_user_profile(m.from_user.id)
    chat_id = m.chat.id
    city = prof["city"]
    mode = "today"

    queues = prof["queues"]
    title_prefix = "Мої черги - "
    show_all_queues = False

    if not queues:
        queues = all_city_queues(city)
        title_prefix = "🌍 Всі черги міста - "
        show_all_queues = True

    if not queues:
        bot.send_message(chat_id, "❌ Немає даних про черги для вашого міста.")
        return

    send_schedules_list(
        chat_id=chat_id,
        queues=queues,
        city=city,
        mode=mode,
        title_prefix=title_prefix,
        show_all_queues=show_all_queues,
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("nav_"))
def graph_navigation(call):
    try:
        _, mode, scope = call.data.split("_")
    except ValueError:
        bot.answer_callback_query(call.id, "Помилка обробки навігації.")
        return

    prof = get_user_profile(call.from_user.id)
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    city = prof["city"]

    if scope == "my":
        queues = prof["queues"]
        title_prefix = "Мої черги - "
        show_all_queues = False

        if not queues:
            bot.answer_callback_query(call.id, "Спочатку додайте свої черги у Профілі!")
            return
    elif scope == "all":
        queues = all_city_queues(city)
        title_prefix = "🌍 Всі черги міста - "
        show_all_queues = True
    else:
        bot.answer_callback_query(call.id, "Невідомий режим.")
        return

    if not queues:
        bot.answer_callback_query(call.id, "Немає черг для відображення.")
        return

    send_schedules_list(
        chat_id=chat_id,
        queues=queues,
        city=city,
        mode=mode,
        title_prefix=title_prefix,
        message_id=message_id,
        show_all_queues=show_all_queues,
    )

    bot.answer_callback_query(call.id)


# ДОПОМОГА / ДОНАТ

@bot.message_handler(func=lambda m: m.text and "допом" in m.text.lower())
def help_msg(m):
    text = (
        "❓ <b>Допомога</b>\n\n"
        "Цей бот підказує, коли у вашому районі буде світло чи темрява.\n"
        "1️⃣ Оберіть місто та свої черги у розділі <b>Профіль</b>.\n"
        "2️⃣ Переглядайте графік у розділі <b>⚡ Графік світла</b>.\n"
        "3️⃣ Увімкніть нагадування за 5/15/30 хв, щоб не пропустити відключення."
    )
    bot.send_message(m.chat.id, text, parse_mode="html", reply_markup=help_keyboard())


@bot.callback_query_handler(func=lambda c: c.data == "menu_back")
def menu_back(call):
    text = "Ви повернулися до головного меню. Оберіть дію знизу 👇"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id)


# СТАРТ БОТА + ВОРКЕР

logging.info(f"Запуск воркера… наступна перевірка через {CHECK_INTERVAL_SEC} секунд.")
global_timer = Timer(CHECK_INTERVAL_SEC, check_and_send_all_alerts)
global_timer.daemon = False
global_timer.start()

print("Bot running…")

while True:
    try:
        bot.infinity_polling()
    except KeyboardInterrupt:
        print("Bot stopped manually")
        global_timer.cancel()

