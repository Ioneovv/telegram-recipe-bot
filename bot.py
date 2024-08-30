import json
import logging
import random
import asyncio
from telegram import Bot
from telegram.ext import ApplicationBuilder
from telegram.error import TelegramError
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
    logging.error("Одно или несколько необходимых значений не установлены в переменных окружения.")
    exit(1)

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
    try:
        # Инициализация бота
        application = ApplicationBuilder().token(TOKEN).build()
        
        # Загрузка рецептов
        recipes = load_recipes()

        # Отправка первого рецепта сразу после запуска
        logging.info("Отправка первого рецепта...")
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
        logging.error(f"Произошла ошибка при запуске основного цикла: {e}")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        logging.error(f"Произошла ошибка при запуске основного цикла: {e}")
