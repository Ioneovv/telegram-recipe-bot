import json
import logging
import random
import asyncio
import requests
from telegram import Bot, InputFile
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
IMAGE_API_URL = os.getenv('IMAGE_API_URL')  # URL API генерации изображений
IMAGE_API_KEY = os.getenv('IMAGE_API_KEY')  # Ключ API генерации изображений

# Проверка переменных окружения
if not TOKEN or not CHAT_ID or not IMAGE_API_URL or not IMAGE_API_KEY:
    logging.error("Токен, ID канала или параметры API не установлены в переменных окружения.")
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

# Получение изображения из API генерации изображений
def get_image_url(description):
    try:
        response = requests.post(
            IMAGE_API_URL,
            headers={"Authorization": f"Bearer {IMAGE_API_KEY}"},
            json={"prompt": description}
        )
        response.raise_for_status()
        image_url = response.json().get('url')
        if not image_url:
            logging.error("Не удалось получить URL изображения из API.")
            return None
        return image_url
    except requests.RequestException as e:
        logging.error(f"Ошибка при запросе к API генерации изображений: {e}")
        return None

# Скачивание изображения
def download_image(image_url):
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        logging.error(f"Ошибка при скачивании изображения: {e}")
        return None

# Асинхронная отправка сообщения в канал
async def send_recipe(bot, chat_id, recipe):
    formatted_text = format_recipe(recipe)
    image_url = get_image_url(formatted_text)
    if image_url:
        image_data = download_image(image_url)
        if image_data:
            try:
                await bot.send_photo(chat_id=chat_id, photo=InputFile(image_data, filename='image.jpg'), caption=formatted_text)
                logging.info("Сообщение с изображением успешно отправлено.")
            except TelegramError as e:
                logging.error(f"Ошибка при отправке сообщения с изображением: {e}")
        else:
            logging.error("Не удалось скачать изображение.")
    else:
        try:
            await bot.send_message(chat_id=chat_id, text=formatted_text)
            logging.info("Сообщение без изображения успешно отправлено.")
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
            await send_recipe(bot, chat_id, recipe)

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

            # Отправка первого рецепта сразу
            if recipes:
                recipe = random.choice(recipes)
                recipes.remove(recipe)  # Удаляем выбранный рецепт из списка
                await send_recipe(application.bot, CHAT_ID, recipe)

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
