import os
import json
from telebot import TeleBot
from dotenv import load_dotenv
import logging

from keyboards import (
    main_menu_reply_keyboard,
    profile_inline_keyboard,
    queues_list_inline_keyboard,
    schedule_inline_keyboard,
    schedule_day_choice_keyboard
)

load_dotenv()
TOKEN = os.getenv("API_KEY")

if not TOKEN:
    raise ValueError("❌ API_KEY не знайдено у ..env файлі")

bot = TeleBot(TOKEN)


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


@bot.message_handler(func=lambda m: m.text == '👤 Профіль')
def handle_profile(message):
    keyboard = profile_inline_keyboard()
    bot.send_message(message.chat.id, "Налаштування профілю:", reply_markup=keyboard)


@bot.message_handler(func=lambda m: m.text == '⚡ Графік світла')
def handle_schedule(message):
    data = load_data()
    today = next(iter(data), None)

    if today:
        queue_numbers = list(data[today].keys())
        keyboard = schedule_inline_keyboard(queue_numbers)
        bot.send_message(message.chat.id, "Обери чергу або скористайся опціями:", reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, "На жаль, дані про графік тимчасово відсутні.")


@bot.message_handler(func=lambda m: m.text == '❓ Допомога')
def handle_help_button(message):
    help_command(message)


@bot.message_handler(func=lambda m: m.text == '👇 Донат')
def handle_donate(message):
    bot.send_message(message.chat.id, "Поки що функція донату у розробці 🙂")


@bot.callback_query_handler(func=lambda call: call.data.startswith('profile_'))
def handle_profile_inline_buttons(call):
    action = call.data.split('_')[-1]
    user_queues = load_user_queues(call.from_user.id)
    all_queues = [str(i) for i in range(1, 13)]  # 1..12

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

logging.basicConfig(level=logging.INFO)

print("Бот запущений. Очікування повідомлень...")
bot.polling(none_stop=True)