import json
import re
import logging
import schedule
import time
import random
from telegram import Bot
from telegram.error import TelegramError
from dotenv import load_dotenv
import os

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

# Загрузить переменные окружения
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHANNEL_ID')

logging.debug(f"TOKEN: {TOKEN}")
logging.debug(f"CHAT_ID: {CHAT_ID}")

# Проверка переменных окружения
if not TOKEN or not CHAT_ID:
    logging.error("Токен или ID канала не установлены в переменных окружения.")
    exit(1)
else:
    logging.info("Переменные окружения успешно загружены.")

# Загрузить рецепты из JSON-файла
def load_recipes():
    try:
        with open('recipes.json', 'r', encoding='utf-8') as file:
            recipes = json.load(file)
            logging.info(f"Рецепты загружены: {len(recipes)} рецептов")
            return recipes
    except FileNotFoundError:
        logging.error("Файл recipes.json не найден.")
        exit(1)
    except json.JSONDecodeError:
        logging.error("Ошибка декодирования JSON в файле recipes.json.")
        exit(1)

# Форматирование текста рецепта
def format_recipe(recipe):
    formatted = recipe.get('title', 'Без названия') + '\n\n'
    formatted += '\n'.join(f"{item['ingredient']} - {item['amount']}" for item in recipe.get('ingredients', [])) + '\n\n'
    formatted += '\n'.join(recipe.get('instructions', []))
    return formatted

# Отправка сообщения в канал
def send_recipe(bot, chat_id, recipe):
    formatted_text = format_recipe(recipe)
    try:
        bot.send_message(chat_id=chat_id, text=formatted_text)
        logging.info("Сообщение успешно отправлено.")
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
    logging.info("Расписание сообщений установлено для отправки в 8:00 и 18:00.")

def main():
    # Инициализация бота
    bot = Bot(token=TOKEN)
    recipes = load_recipes()
    # Планирование сообщений
    schedule_messages(bot, CHAT_ID, recipes)
    # Запуск планировщика
    logging.info("Запуск планировщика.")
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    main()
