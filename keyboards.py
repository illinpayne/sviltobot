from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_reply_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)

    btn_profile = KeyboardButton('👤 Профіль')
    keyboard.add(btn_profile)

    btn_schedule = KeyboardButton('⚡ Графік світла')
    keyboard.add(btn_schedule)

    btn_donate = KeyboardButton('👇 Донат')
    keyboard.add(btn_donate)

    btn_help = KeyboardButton('❓ Допомога')
    keyboard.add(btn_help)

    return keyboard


def profile_inline_keyboard():
    keyboard = InlineKeyboardMarkup()

    keyboard.add(InlineKeyboardButton('➕ Додати чергу', callback_data='profile_add_queue'))
    keyboard.add(InlineKeyboardButton('📋 Мої черги', callback_data='profile_my_queues'))
    keyboard.add(InlineKeyboardButton('🔔 Сповіщення', callback_data='profile_notifications'))
    keyboard.add(InlineKeyboardButton('⏰ Нагадування', callback_data='profile_reminders'))

    return keyboard


def queues_list_inline_keyboard(user_queues, all_queues):
    """
    user_queues: список черг, які вже вибрав користувач
    all_queues: список всіх можливих черг
    """
    keyboard = InlineKeyboardMarkup(row_width=2)

    # Додати кнопки для черг
    for q in all_queues:
        if q in user_queues:
            keyboard.add(InlineKeyboardButton(f'✅ Черга {q}', callback_data=f'queue_selected_{q}'))
        else:
            keyboard.add(InlineKeyboardButton(f'⬜ Черга {q}', callback_data=f'queue_select_{q}'))

    # Редагування та видалення для черг, якщо вони вже додані
    if user_queues:
        keyboard.add(
            InlineKeyboardButton('📝 Редагувати черги', callback_data='queues_edit')
        )

    keyboard.add(InlineKeyboardButton('⬅️ Назад', callback_data='back_to_profile'))

    return keyboard


def schedule_inline_keyboard(queue_numbers):
    keyboard = InlineKeyboardMarkup()

    for num in queue_numbers:
        keyboard.add(InlineKeyboardButton(f'Черга {num}', callback_data=f'schedule_select_{num}'))

    return keyboard


def schedule_day_choice_keyboard(queue_num):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
    InlineKeyboardButton("📅 На сьогодні", callback_data=f'schedule_day_today_{queue_num}')
    )
    keyboard.add(
    InlineKeyboardButton("📆 На завтра", callback_data=f'schedule_day_tomorrow_{queue_num}')
    )
    return keyboard




