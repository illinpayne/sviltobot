# main.py

import logging
from datetime import datetime, timedelta
from threading import Timer

from telebot import TeleBot

from config import (
    TOKEN,
    CHECK_INTERVAL_SEC,
    load_users,
    get_schedule_hash,
    get_user_profile,
    get_area_title,
    get_outage_intervals_for_queue,
    list_available_areas,
    SENT_REMINDERS_LOG,
    LAST_SCHEDULE_HASH,
    logger,
)
from handlers import register_handlers

# --- ІНІЦІАЛІЗАЦІЯ БОТА ---

bot = TeleBot(TOKEN)
global_timer = None

# Реєстрація хендлерів з окремого файлу
register_handlers(bot)


# --- ФОНОВИЙ ВОРКЕР ---

def send_schedule_change_notification(chat_id, area_code):
    """Надсилає сповіщення про зміну графіка."""
    msg = (
        f"🚨 <b>Графік оновлено!</b>\n"
        f"Область: <b>{get_area_title(area_code)}</b>\n\n"
        f"Перевірте меню <b>⚡ Графік світла</b>."
    )
    bot.send_message(chat_id, msg, parse_mode="html")


def check_and_send_all_alerts():
    """Фонова функція для перевірки змін графіка та нагадувань."""
    global global_timer

    # Перезапускаємо таймер на наступну ітерацію
    global_timer = Timer(CHECK_INTERVAL_SEC, check_and_send_all_alerts)
    global_timer.daemon = False
    global_timer.start()

    try:
        now = datetime.now()
        users = load_users()

        # 1. Перевірка змін графіка по всіх областях
        areas = list_available_areas()
        for area_code in areas:
            schedule_hash = get_schedule_hash(area_code)

            if area_code not in LAST_SCHEDULE_HASH:
                LAST_SCHEDULE_HASH[area_code] = schedule_hash
            elif schedule_hash != LAST_SCHEDULE_HASH[area_code]:
                logger.warning(f"Зміна графіка для {area_code}!")
                for uid_str, profile in users.items():
                    if profile.get("area") == area_code and profile.get("notifications_enabled"):
                        send_schedule_change_notification(int(uid_str), area_code)
                LAST_SCHEDULE_HASH[area_code] = schedule_hash

        # 2. Перевірка нагадувань
        reminder_window_start = now
        reminder_window_end = now + timedelta(seconds=CHECK_INTERVAL_SEC)

        today_key = now.strftime("%Y%m%d")
        if today_key not in SENT_REMINDERS_LOG:
            SENT_REMINDERS_LOG[today_key] = {}

        for uid_str, profile in users.items():
            uid = int(uid_str)
            profile = get_user_profile(uid) # Отримуємо актуальний профіль

            offsets = profile.get("reminder_offsets", [])
            if not offsets:
                continue

            user_area = profile.get("area")
            queues = profile.get("queues", [])

            for queue in queues:
                intervals = get_outage_intervals_for_queue(user_area, queue)

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

                        sent_for_user = SENT_REMINDERS_LOG[today_key].setdefault(uid_str, [])
                        if reminder_id in sent_for_user:
                            continue

                        msg = (
                            f"💡 <b>СКОРО ВІДКЛЮЧЕННЯ</b>\n"
                            f"Область: <b>{get_area_title(user_area)}</b>\n"
                            f"Черга <b>{queue}</b>\n"
                            f"Початок о <b>{start_dt.strftime('%H:%M')}</b>\n"
                            f"Нагадування за <b>{offset_int} хв</b>."
                        )
                        try:
                            bot.send_message(uid, msg, parse_mode="html")
                            sent_for_user.append(reminder_id)
                            logger.info(f"Надіслано нагадування користувачу {uid} для черги {queue}, offset={offset_int}")
                        except Exception as e:
                            logger.error(f"Не вдалося надіслати нагадування {uid}: {e}")

        logger.info("Воркер завершив перевірку.")

    except Exception as e:
        logger.error(f"Помилка у воркері: {e}")


# --- ЗАПУСК БОТА + ВОРКЕР ---

if __name__ == "__main__":
    logger.info(f"Запуск воркера… наступна перевірка через {CHECK_INTERVAL_SEC} секунд.")
    # Перший виклик запускає логіку, а також встановлює Timer на наступний запуск
    check_and_send_all_alerts()

    print("Bot running…")

    try:
        bot.polling()
    except KeyboardInterrupt:
        print("Bot stopped manually")
        if global_timer:
            global_timer.cancel()
    except Exception as e:
        logger.error(f"Критична помилка bot.polling: {e}")
        if global_timer:
            global_timer.cancel()