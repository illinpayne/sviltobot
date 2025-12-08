import telebot
import creds
import json
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup

from keyboards import (
    main_menu_reply_keyboard,
    profile_inline_keyboard,
    queues_list_inline_keyboard,
    schedule_inline_keyboard,
    schedule_day_choice_keyboard
)

bot = telebot.TeleBot(creds.api_key)

# Допоміжні функції
def load_data():
    try:
        with open("storage.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def load_user_queues(user_id):
    try:
        with open("users.json", "r", encoding="utf-8") as f:
            users = json.load(f)
        return users.get(str(user_id), [])
    except FileNotFoundError:
        return []

def save_user_queues(user_id, queues):
    try:
        with open("users.json", "r", encoding="utf-8") as f:
            users = json.load(f)
    except FileNotFoundError:
        users = {}
    users[str(user_id)] = queues
    with open("users.json", "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


# Команди
@bot.message_handler(commands=['start'])
def start(msg):
    keyboard = main_menu_reply_keyboard()
    bot.send_message(
        msg.chat.id,
        "Привіт! Я СвітлоБот. Скористайся кнопками нижче:",
        reply_markup=keyboard
    )

@bot.message_handler(commands=['help'])
def help_command(message):
    keyboard = main_menu_reply_keyboard()
    bot.send_message(
        message.chat.id,
        "<b>Текст допомоги</b>",
        parse_mode='html',
        reply_markup=keyboard
    )

# Обробка кнопок головного меню
@bot.message_handler(func=lambda message: message.text == '👤 Профіль')
def handle_profile(message):
    keyboard = profile_inline_keyboard()
    bot.send_message(
        message.chat.id,
        "Налаштування профілю:",
        reply_markup=keyboard
    )

@bot.message_handler(func=lambda message: message.text == '⚡ Графік світла')
def handle_schedule(message):
    data = load_data()
    today = next(iter(data), None)
    if today:
        queue_numbers = list(data[today].keys())
        keyboard = schedule_inline_keyboard(queue_numbers)
        bot.send_message(
            message.chat.id,
            "Обери чергу або скористайся опціями:",
            reply_markup=keyboard
        )
    else:
        bot.send_message(message.chat.id, "На жаль, дані про графік тимчасово відсутні.")

@bot.message_handler(func=lambda message: message.text == '👇 Донат')
def handle_donate(message):
    bot.send_message(message.chat.id, "Поки що функція донату у розробці 🙂")

@bot.message_handler(func=lambda message: message.text == '❓ Допомога')
def handle_help_button(message):
    help_command(message)

# Обробка callback кнопок профілю
@bot.callback_query_handler(func=lambda call: call.data.startswith('profile_'))
def handle_profile_inline_buttons(call):
    action = call.data.split('_')[-1]
    user_queues = load_user_queues(call.from_user.id)
    all_queues = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']

    if action == 'my_queues':
        keyboard = queues_list_inline_keyboard(user_queues, all_queues)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Ваші черги:",
            reply_markup=keyboard
        )
    elif action == 'notifications':
        bot.answer_callback_query(call.id, "Сповіщення увімкнено/вимкнено")
    elif action == 'add_queue':
        bot.answer_callback_query(call.id, "Додати нову чергу можна через 'Мої черги'")
    else:
        bot.answer_callback_query(call.id, f"Дія: {action} (у розробці)")

@bot.callback_query_handler(func=lambda call: call.data.startswith('back_to_profile'))
def handle_back_button(call):
    keyboard = profile_inline_keyboard()
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Налаштування профілю:",
        reply_markup=keyboard
    )
    bot.answer_callback_query(call.id)

# Обробка вибору черг
@bot.callback_query_handler(func=lambda call: call.data.startswith('queue_'))
def handle_queue_buttons(call):
    user_queues = load_user_queues(call.from_user.id)
    parts = call.data.split('_')
    action = parts[0]
    queue_num = parts[-1]

    if action == 'queue' or action == 'queue_select':
        if queue_num not in user_queues:
            user_queues.append(queue_num)
        else:
            user_queues.remove(queue_num)
        save_user_queues(call.from_user.id, user_queues)
        all_queues = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
        keyboard = queues_list_inline_keyboard(user_queues, all_queues)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=keyboard)

    elif action == 'queue_selected':
        bot.answer_callback_query(call.id, f"Черга {queue_num} вже вибрана ✅")
    bot.answer_callback_query(call.id)

# Обробка вибору графіку світла
@bot.callback_query_handler(func=lambda call: call.data.startswith('schedule_select_'))
def handle_schedule_inline_buttons(call):
    queue_num = call.data.replace("schedule_select_", "")
    keyboard = schedule_day_choice_keyboard(queue_num)
    bot.edit_message_text(
        f"Ви обрали чергу *{queue_num}*.\nОберіть день:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode='Markdown',
        reply_markup=keyboard
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('schedule_day_'))
def handle_day_buttons(call):
    data = load_data()
    parts = call.data.split('_')
    day_type = parts[2]
    queue_num = parts[3]

    today = datetime.now().date()
    selected_date = today if day_type == "today" else today + timedelta(days=1)
    selected_date_str = selected_date.strftime("%d.%m.%Y")

    if selected_date_str not in data or queue_num not in data[selected_date_str]:
        bot.answer_callback_query(call.id, "Даних немає ❗")
        return

    times = data[selected_date_str][queue_num]
    times_text = "\n".join([f"• {t}" for t in times]) if times else "Немає відключень 👍"
    text = f"📅 Графік на {selected_date_str}\nЧерга *{queue_num}*:\n\n{times_text}"

    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, text, parse_mode='Markdown')


bot.polling(none_stop=True)






