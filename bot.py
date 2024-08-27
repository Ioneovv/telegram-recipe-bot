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
    # Получаем данные
    title = recipe.get('title', 'Без названия')
    ingredients = recipe.get('ingredients', [])
    instructions = recipe.get('instructions', [])

    # Преобразуем список ингредиентов в строку
    ingredients_str = '\n'.join(f"{item['ingredient']} - {item['amount']}" for item in ingredients) if isinstance(ingredients, list) else ingredients
    # Преобразуем список инструкций в строку
    instructions_str = '\n'.join(instructions) if isinstance(instructions, list) else instructions

    # Форматируем текст рецепта
    formatted = title + '\n\n'
    formatted += re.sub(r'[\[\]\{\}]', '', ingredients_str) + '\n\n'
    formatted += re.sub(r'[\[\]\{\}]', '', instructions_str)
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
        logging.info("Выбран рецепт для отправки.")
        send_recipe(bot, chat_id, recipe)

    # Настроить отправку сообщений каждую минуту
    schedule.every(1).minute.do(send_random_recipe)
    logging.info("Расписание сообщений установлено для отправки каждую минуту.")

def main():
    # Инициализация бота
    bot = Bot(token=TOKEN)

    try:
        # Проверка подключения к Telegram API
        bot.get_me()
        logging.info("Бот успешно подключен к Telegram API.")
    except TelegramError as e:
        logging.error(f"Ошибка при подключении к Telegram API: {e}")
        exit(1)
    
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
