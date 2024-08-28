import json
import logging
import random
import asyncio
from telegram import Bot
from telegram.error import TelegramError
from telegram.ext import Application, ApplicationBuilder
from dotenv import load_dotenv
import os

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

# Загрузить переменные окружения
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHANNEL_ID')

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

# Асинхронная отправка сообщения в канал
async def send_recipe(bot, chat_id, recipe):
    formatted_text = format_recipe(recipe)
    try:
        await bot.send_message(chat_id=chat_id, text=formatted_text)
        logging.info("Сообщение успешно отправлено.")
    except TelegramError as e:
        logging.error(f"Ошибка при отправке сообщения: {e}")

# Асинхронная функция для выполнения задач в заданное время
async def periodic_task(bot, chat_id, recipes):
    while True:
        now = asyncio.get_event_loop().time()
        next_run = (now + 3600*8) % (24*3600)  # например, 8 часов позже
        await asyncio.sleep(next_run)
        
        if not recipes:
            logging.info("Рецепты закончились. Перезагружаем список...")
            recipes.extend(load_recipes())  # Перезагружаем список рецептов
        recipe = random.choice(recipes)
        recipes.remove(recipe)  # Удаляем выбранный рецепт из списка
        await send_recipe(bot, chat_id, recipe)

async def main():
    # Инициализация бота
    application = ApplicationBuilder().token(TOKEN).build()
    recipes = load_recipes()

    # Запуск периодической задачи
    logging.info("Запуск периодической задачи.")
    await periodic_task(application.bot, CHAT_ID, recipes)

if __name__ == '__main__':
    asyncio.run(main())
