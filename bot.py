import json
import re
from datetime import datetime
import logging
import schedule
import time
from telegram import Bot
from telegram.ext import Updater

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Загрузить рецепты из JSON-файла
def load_recipes():
    with open('recipes.json', 'r', encoding='utf-8') as file:
        return json.load(file)

# Форматирование текста рецепта
def format_recipe(recipe):
    formatted = recipe['title'] + '\n\n'
    formatted += re.sub(r'[\[\]\{\}]', '', recipe['ingredients']) + '\n\n'
    formatted += re.sub(r'[\[\]\{\}]', '', recipe['instructions'])
    return formatted

# Отправка сообщения в канал
def send_recipe(bot, chat_id, recipe):
    formatted_text = format_recipe(recipe)
    bot.send_message(chat_id=chat_id, text=formatted_text)

# Планирование отправки рецептов
def schedule_messages(bot, chat_id, recipes):
    schedule.every().day.at("08:00").do(lambda: send_recipe(bot, chat_id, recipes[0]))
    schedule.every().day.at("18:00").do(lambda: send_recipe(bot, chat_id, recipes[1]))

def main():
    # Укажи токен бота и ID канала
    TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
    CHAT_ID = 'YOUR_CHANNEL_ID'

    # Инициализация бота
    bot = Bot(token=TOKEN)
    recipes = load_recipes()

    # Планирование сообщений
    schedule_messages(bot, CHAT_ID, recipes)

    # Запуск планировщика
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    main()
