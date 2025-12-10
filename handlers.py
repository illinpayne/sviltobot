# handlers.py

from telebot import TeleBot
import telebot
import logging

from keyboards import (
    main_menu_keyboard,
    profile_keyboard,
    queues_keyboard,
    schedule_navigation_keyboard,
    help_keyboard,
    region_select_keyboard,
    area_select_keyboard,
    reminders_keyboard,
)

from config import (
    get_user_profile,
    save_user_profile,
    get_area_title,
    all_area_queues,
    list_available_areas,
    REGIONS,
    build_schedule_message,
)

# Налаштування рівня логування telebot
telebot.logger.setLevel(logging.DEBUG)


def register_handlers(bot: TeleBot):
    """Реєструє всі хендлери для переданого об'єкта бота."""

    # --- ДОПОМІЖНА ФУНКЦІЯ ДЛЯ ВІДОБРАЖЕННЯ ГРАФІКА ---

    def send_schedules_list(chat_id, queues, area_code, mode, title_prefix="", message_id=None, show_all_queues=False):
        text = build_schedule_message(queues, area_code, mode, title_prefix)
        kb = schedule_navigation_keyboard(mode, show_all_queues)

        if message_id:
            bot.edit_message_text(text, chat_id, message_id, parse_mode="html", reply_markup=kb)
        else:
            bot.send_message(chat_id, text, parse_mode="html", reply_markup=kb)

    # --- ХЕНДЛЕРИ БОТА ---

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
            f"Область: <b>{get_area_title(prof['area'])}</b>\n"
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
        area_code = prof["area"]
        all_q = all_area_queues(area_code)

        kb = queues_keyboard(prof["queues"], all_q)

        bot.edit_message_text(
            "Оберіть ваші черги:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("queue_toggle_"))
    def queue_toggle(call):
        prof = get_user_profile(call.from_user.id)
        all_q = all_area_queues(prof["area"])

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
            f"Область: <b>{get_area_title(prof['area'])}</b>\n"
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
            f"Область: <b>{get_area_title(prof['area'])}</b>\n"
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

    # --- ЛОГІКА ВИБОРУ ОБЛАСТІ ---

    @bot.callback_query_handler(func=lambda c: c.data == "profile_change_area")
    def profile_change_area(call):
        if not list_available_areas():
            bot.answer_callback_query(call.id, "Немає доступних областей.")
            return

        kb = region_select_keyboard()
        bot.edit_message_text(
            "🌍 Оберіть регіон України:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb,
        )
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("region_select_"))
    def select_region(call):
        region_code = call.data.split("_", 2)[-1]

        if region_code not in REGIONS:
            bot.answer_callback_query(call.id, "Невідомий регіон.")
            return

        prof = get_user_profile(call.from_user.id)
        kb = area_select_keyboard(region_code, prof["area"])

        region_title = REGIONS.get(region_code, {}).get("title", region_code)

        bot.edit_message_text(
            f"📍 Оберіть область у регіоні {region_title}:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb,
        )
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "back_regions")
    def back_regions(call):
        kb = region_select_keyboard()
        bot.edit_message_text(
            "🌍 Оберіть регіон України:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb,
        )
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("area_set_"))
    def set_area(call):
        area_code = call.data.split("_", 2)[-1]
        available = list_available_areas()
        if area_code not in available:
            bot.answer_callback_query(call.id, "Область більше недоступна.")
            return

        prof = get_user_profile(call.from_user.id)
        prof["area"] = area_code
        prof["queues"] = []  # при зміні області скидаємо черги
        save_user_profile(call.from_user.id, prof)

        # Повернення до профілю
        queues = "не вибрані"
        text = (
            f"👤 <b>Ваш профіль</b>\n\n"
            f"ID: <code>{call.from_user.id}</code>\n"
            f"Область: <b>{get_area_title(prof['area'])}</b>\n"
            f"📟 Черги: {queues}"
        )

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="html",
            reply_markup=profile_keyboard(prof),
        )

        bot.answer_callback_query(call.id, f"Область змінено на {get_area_title(area_code)}")

    # --- НАГАДУВАННЯ ---

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
        area_code = prof["area"]
        mode = "today"

        queues = prof["queues"]
        title_prefix = "Мої черги - "
        show_all_queues = False

        if not queues:
            queues = all_area_queues(area_code)
            title_prefix = "🌍 Всі черги області - "
            show_all_queues = True

        if not queues:
            bot.send_message(chat_id, "❌ Немає даних про черги для вашої області.")
            return

        send_schedules_list(
            chat_id=chat_id,
            queues=queues,
            area_code=area_code,
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
        area_code = prof["area"]

        if scope == "my":
            queues = prof["queues"]
            title_prefix = "Мої черги - "
            show_all_queues = False

            if not queues:
                bot.answer_callback_query(call.id, "Спочатку додайте свої черги у Профілі!")
                return
        elif scope == "all":
            queues = all_area_queues(area_code)
            title_prefix = "🌍 Всі черги області - "
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
            area_code=area_code,
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
            "1️⃣ Оберіть Область та свої Черги у розділі 👤 Мій профіль.\n"
            "2️⃣ Переглядайте графік у розділі ⚡ Графік світла.\n"
            "3️⃣ Увімкніть нагадування за 5/10/15/30/60 хв, щоб не пропустити відключення."
        )
        bot.send_message(m.chat.id, text, parse_mode="html", reply_markup=help_keyboard())

    @bot.callback_query_handler(func=lambda c: c.data == "menu_back")
    def menu_back(call):
        chat_id = call.message.chat.id
        message_id = call.message.message_id

        # 1. Редагуємо існуюче повідомлення, щоб видалити INLINE-клавіатуру.
        # Якщо цього не зробити, користувач бачитиме старе повідомлення з кнопками.
        try:
            bot.edit_message_text(
                "🏠 Ви повернулися до головного меню.",
                chat_id,
                message_id,
                reply_markup=None  # <--- Ключова зміна: видаляємо Inline-клавіатуру
            )
        except Exception as e:
            # Пропускаємо помилку, якщо повідомлення не змінилося (наприклад, вже було відредаговано)
            logging.warning(f"Помилка при спробі видалити клавіатуру: {e}")

            # 2. Надсилаємо НОВЕ повідомлення, яке матиме REPLY-клавіатуру внизу екрана.
        text = "Оберіть дію знизу 👇"
        bot.send_message(chat_id, text, reply_markup=main_menu_keyboard())

        bot.answer_callback_query(call.id)