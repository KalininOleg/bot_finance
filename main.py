import telebot
import sqlite3 as sq
from telebot import types
from bot_info import X

bot = telebot.TeleBot(X)
# создание бд
connection = sq.connect("my_database.db", check_same_thread=False)
cursor = connection.cursor()

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS Expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    amount INTEGER NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
"""
)

connection.commit()

# хранение состояния пользователей
user_states = {}


@bot.message_handler(commands=["start"])
def send_welcome(message):
    """Старт. Приветствуем и создаем клавиатуру"""
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button1 = types.KeyboardButton("Добавить")
    button2 = types.KeyboardButton("Удалить")
    button3 = types.KeyboardButton("Сколько потрачено?")
    keyboard.add(button1, button2, button3)

    bot.reply_to(message, "Привет! Выбери действие:", reply_markup=keyboard)


@bot.message_handler(func=lambda message: message.text == "Добавить")
def ask_expense_amount(message):
    """Запрашивает у пользователя сумму трат."""
    bot.reply_to(message, "Сколько потратил?")
    user_states[message.chat.id] = "waiting_for_amount"


@bot.message_handler(
    func=lambda message: message.chat.id in user_states
    and user_states[message.chat.id] == "waiting_for_amount"
)
def add_expense(message):
    """Добавляет сумму траты в БД."""
    try:
        amount = int(message.text)
        username = (
            message.from_user.username or message.from_user.first_name
        )  # Имя пользователя

        cursor.execute(
            "INSERT INTO Expenses (username, amount) VALUES (?, ?)"
            , (username, amount)
        )
        connection.commit()

        bot.reply_to(message, f"Записал {amount} трат от {username}")
        del user_states[message.chat.id]  # Убираем пользователя из ожидания
    except ValueError:
        bot.reply_to(message, "Введите сумму числом")


@bot.message_handler(func=lambda message: message.text == "Сколько потрачено?")
def get_total_expense(message):
    """Выводит сумму трат."""
    cursor.execute("SELECT SUM(amount) FROM Expenses")
    total = cursor.fetchone()[0]
    total = total if total else 0
    bot.reply_to(message, f"Всего потрачено: {total}")


@bot.message_handler(func=lambda message: True)
def unknown_command(message):
    """Обрабатывает неизвестные команды."""
    bot.reply_to(message, "Не понял команду. Используй кнопки!")


bot.polling()
