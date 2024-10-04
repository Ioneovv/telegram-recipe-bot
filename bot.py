import json
import logging
import random
import asyncio
from telegram import Bot, Poll
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

# Асинхронная отправка опроса
async def send_poll(bot, chat_id):
    question = "Какие рецепты вам больше нравятся? 🍽️"
    options = [
        "🍰 Десерты",
        "🥗 Салаты",
        "🍛 Горячее",
        "🍲 Супы",
        "🍳 Завтраки"
    ]
    
    try:
        message = await bot.send_poll(chat_id=chat_id, question=question, options=options, is_anonymous=False)
        logging.info("Опрос успешно отправлен.")
        return message.poll.id  # Возвращаем идентификатор опроса для последующей обработки
    except TelegramError as e:
        logging.error(f"Ошибка при отправке опроса: {e}")
        return None

# Получить выбранную категорию на основе результатов опроса
async def get_poll_results(bot, poll_id):
    # Получить результаты опроса (эту часть можно доработать при наличии API для получения результата голосования)
    pass  # Для примера оставим заглушку

# Асинхронная функция для выполнения задач в заданное время
async def periodic_task(bot, chat_id, recipes, interval_hours=8):  # Изменённый интервал на 8 часов
    post_count = 0  # Счётчик отправленных постов
    selected_category = None  # Хранение выбранной категории

    while True:
        try:
            if not recipes:
                logging.info("Рецепты закончились. Перезагружаем список...")
                recipes.extend(load_recipes())  # Перезагружаем список рецептов

            # Фильтруем рецепты по выбранной категории, если она установлена
            if selected_category:
                filtered_recipes = [recipe for recipe in recipes if recipe.get('category') == selected_category]
                if filtered_recipes:
                    recipe = random.choice(filtered_recipes)
                else:
                    recipe = random.choice(recipes)
            else:
                recipe = random.choice(recipes)

            recipes.remove(recipe)  # Удаляем выбранный рецепт из списка
            await send_recipe(bot, chat_id, recipe)

            post_count += 1  # Увеличиваем счетчик

            # После каждого пятого поста отправляем опрос
            if post_count >= 5:
                poll_id = await send_poll(bot, chat_id)
                if poll_id:
                    # Здесь можно реализовать логику получения и обработки результатов опроса
                    selected_category = "Десерты"  # Пример: присвоим значение вручную для тестирования
                    logging.info(f"Следующая тема рецептов: {selected_category}")
                post_count = 0  # Сбрасываем счетчик после опроса

            logging.info(f"Следующее сообщение будет отправлено через {interval_hours} часов.")
            await asyncio.sleep(interval_hours * 3600)  # Пауза на указанные часы
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
