import json
import logging
import random
import asyncio
import aiohttp  # Для асинхронных HTTP-запросов
from telegram import Bot
from telegram.error import TelegramError
from telegram.ext import ApplicationBuilder
from dotenv import load_dotenv
import os

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

# Загрузить переменные окружения
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHANNEL_ID')
IMAGE_API_URL = os.getenv('IMAGE_API_URL')
IMAGE_API_KEY = os.getenv('IMAGE_API_KEY')

# Проверка переменных окружения
if not TOKEN or not CHAT_ID or not IMAGE_API_URL or not IMAGE_API_KEY:
    logging.error("Одно или несколько необходимых значений не установлены в переменных окружения.")
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

# Асинхронная функция для генерации изображения
async def generate_image(recipe_title):
    headers = {
        'Authorization': f'Bearer {IMAGE_API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        'prompt': f'{recipe_title} на тарелке, красиво и реалистично, без лишних деталей',
        'negative_prompt': 'некачественные изображения, дополнительные предметы',
        'width': 512,
        'height': 512
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(IMAGE_API_URL, headers=headers, json=data) as response:
            if response.status == 200:
                result = await response.json()
                image_url = result.get('image_url')
                return image_url
            else:
                logging.error(f"Ошибка при генерации изображения: {response.status}")
                return None

# Асинхронная отправка сообщения с изображением в канал
async def send_recipe_with_image(bot, chat_id, recipe):
    formatted_text = format_recipe(recipe)
    image_url = await generate_image(recipe.get('title', 'Без названия'))
    
    try:
        if image_url:
            await bot.send_photo(chat_id=chat_id, photo=image_url, caption=formatted_text)
        else:
            await bot.send_message(chat_id=chat_id, text=formatted_text)
        logging.info("Сообщение успешно отправлено.")
    except TelegramError as e:
        logging.error(f"Ошибка при отправке сообщения: {e}")

# Асинхронная функция для выполнения задач в заданное время
async def periodic_task(bot, chat_id, recipes, interval_hours=6):
    while True:
        try:
            if not recipes:
                logging.info("Рецепты закончились. Перезагружаем список...")
                recipes.extend(load_recipes())  # Перезагружаем список рецептов

            recipe = random.choice(recipes)
            recipes.remove(recipe)  # Удаляем выбранный рецепт из списка
            await send_recipe_with_image(bot, chat_id, recipe)

            logging.info(f"Следующее сообщение будет отправлено через {interval_hours} часов.")
            await asyncio.sleep(interval_hours * 3600)  # Пауза на указанное количество часов
        except Exception as e:
            logging.error(f"Произошла ошибка в периодической задаче: {e}")
            await asyncio.sleep(60)  # Пауза перед повторной попыткой

async def main():
    while True:
        try:
            # Инициализация бота
            application = ApplicationBuilder().token(TOKEN).build()
            recipes = load_recipes()

            # Отправка первого рецепта сразу после запуска
            logging.info("Отправка первого рецепта...")
            recipe = random.choice(recipes)
            recipes.remove(recipe)  # Удаляем выбранный рецепт из списка
            await send_recipe_with_image(application.bot, CHAT_ID, recipe)

            # Запуск периодической задачи
            logging.info("Запуск периодической задачи.")
            task = asyncio.create_task(periodic_task(application.bot, CHAT_ID, recipes))

            # Запуск бота
            await application.start()
            await task
        except Exception as e:
            logging.error(f"Произошла ошибка в основном цикле: {e}")
            await asyncio.sleep(60)  # Пауза перед повторной попыткой

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        logging.error(f"Произошла ошибка при запуске основного цикла: {e}")
