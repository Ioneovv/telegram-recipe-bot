import json
import re
import logging
import schedule
import time
import random
from telegram import Bot
from telegram.error import TelegramError  # Импортируем TelegramError из telegram.error
from dotenv import load_dotenv
import os

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Загрузить переменные окружения
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHANNEL_ID')

# Проверка переменных окружения
if not TOKEN or not CHAT_ID:
    logging.error("Токен или ID канала не установлены в переменных окружения.")
    exit(1)

# Загрузить рецепты из JSON-файла
def load_recipes():
    try:
        with open('recipes.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        logging.error("Файл recipes.json не найден.")
        exit(1)
    except json.JSONDecodeError:
        logging.error("Ошибка декодирования JSON в файле recipes.json.")
        exit(1)

# Форматирование текста рецепта
def format_recipe(recipe):
    formatted = recipe.get('title', 'Без названия') + '\n\n'
    formatted += re.sub(r'[\[\]\{\}]', '', recipe.get('ingredients', 'Без ингредиентов')) + '\n\n'
    formatted += re.sub(r'[\[\]\{\}]', '', recipe.get('instructions', 'Без инструкций'))
    return formatted

# Отправка сообщения в канал
def send_recipe(bot, chat_id, recipe):
    formatted_text = format_recipe(recipe)
    try:
        bot.send_message(chat_id=chat_id, text=formatted_text)
    except TelegramError as e:
        logging.error(f"Ошибка при отправке сообщения: {e}")

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
