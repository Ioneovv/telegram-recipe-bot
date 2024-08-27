import json
import re
import logging
import schedule
import time
import random
from telegram import Bot
from dotenv import load_dotenv
import os

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Загрузить переменные окружения
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHANNEL_ID')

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
    def send_random_recipe():
        if not recipes:
            logging.info("Рецепты закончились. Перезагружаем список...")
            recipes.extend(load_recipes())  # Перезагружаем список рецептов

        recipe = random.choice(recipes)
        recipes.remove(recipe)  # Удаляем выбранный рецепт из списка
        send_recipe(bot, chat_id, recipe)

    schedule.every().day.at("08:00").do(send_random_recipe)
    schedule.every().day.at("18:00").do(send_random_recipe)

def main():
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
