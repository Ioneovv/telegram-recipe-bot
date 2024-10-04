import logging
import re
import json
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackContext, CommandHandler, CallbackQueryHandler
import requests

# Логирование
logging.basicConfig(level=logging.INFO)

# Глобальная переменная для хранения рецептов
recipes = []

# Эмодзи для категорий
CATEGORY_EMOJIS = {
    "Салаты": "🥗",
    "Супы": "🍲",
    "Десерты": "🍰",
    "Основные блюда": "🍽",
    "Закуски": "🥪",
    "Напитки": "🥤",
}

# Загрузка рецептов
def load_recipes():
    try:
        with open('recipes.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logging.error("Ошибка загрузки или обработки recipes.json")
        return []

# Форматирование рецепта
def format_recipe(recipe):
    recipe_text = f"🍽 **{recipe['title']}**\n\n"
    recipe_text += "📝 **Ингредиенты:**\n"
    for ingredient in recipe.get('ingredients', []):
        amount = ingredient.get('amount', '')
        recipe_text += f"🔸 {ingredient['ingredient']:20} {amount}\n"
    recipe_text += "\n🧑‍🍳 **Приготовление:**\n"
    for i, step in enumerate(recipe.get('instructions', []), start=1):
        recipe_text += f"{i}. {step}\n"
    return recipe_text

# Получение категорий
def get_categories():
    return sorted(set(recipe.get('category') for recipe in recipes))

# Поиск рецептов
def search_recipes(query):
    return [recipe for recipe in recipes if query.lower() in recipe['title'].lower()]

# Функция составления меню
def create_weekly_menu():
    selected_recipes = random.sample(recipes, 7)
    menu = "\n".join([f"{i + 1}. {recipe['title']}" for i, recipe in enumerate(selected_recipes)])
    return f"📅 **Ваше меню на неделю:**\n{menu}"

# Команды и обработчики
async def start(update: Update, context: CallbackContext):
    global recipes
    recipes = load_recipes()
    if not recipes:
        await update.message.reply_text("Не удалось загрузить рецепты. Пожалуйста, попробуйте позже.")
        return

    categories = get_categories()
    keyboard = [
        [InlineKeyboardButton(f"{CATEGORY_EMOJIS.get(category, '🍴')} {category}", callback_data=f'category_{category}')]
        for category in categories
    ]
    keyboard.append([InlineKeyboardButton("📅 Составить меню на неделю", callback_data='weekly_menu')])
    keyboard.append([InlineKeyboardButton("🔍 Поиск рецептов", callback_data='search')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Выберите категорию рецептов:', reply_markup=reply_markup)

async def category_button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    category = query.data.split('_')[1]

    recipes_in_category = [recipe for recipe in recipes if recipe['category'] == category]
    if not recipes_in_category:
        await query.message.reply_text("Нет рецептов в этой категории.")
        return

    keyboard = [[InlineKeyboardButton(recipe['title'], callback_data=f'recipe_{recipes.index(recipe)}')] for recipe in recipes_in_category]
    keyboard.append([InlineKeyboardButton("🏠 Домой", callback_data='home')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.edit_text(f"Рецепты категории: {category}", reply_markup=reply_markup)

async def recipe_button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    recipe_index = int(query.data.split('_')[1])
    recipe = recipes[recipe_index]
    recipe_text = format_recipe(recipe)

    keyboard = [
        [InlineKeyboardButton("Назад", callback_data=f'category_{recipe["category"]}')],
        [InlineKeyboardButton("🏠 Домой", callback_data='home')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.edit_text(recipe_text, reply_markup=reply_markup)

async def weekly_menu(update: Update, context: CallbackContext):
    menu = create_weekly_menu()
    await update.callback_query.message.reply_text(menu)

async def search_handler(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("Введите название или ингредиент для поиска:")
    return 'SEARCH'

async def handle_search(update: Update, context: CallbackContext):
    query = update.message.text
    results = search_recipes(query)
    if not results:
        await update.message.reply_text("Ничего не найдено.")
        return

    keyboard = [[InlineKeyboardButton(recipe['title'], callback_data=f'recipe_{recipes.index(recipe)}')] for recipe in results]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Результаты поиска:", reply_markup=reply_markup)

async def main():
    global recipes
    recipes = load_recipes()
    
    app = ApplicationBuilder().token("6953692387:AAEm-p8VtfqdmkHtbs8hxZWS-XNkdRN2lRE").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(category_button, pattern=r'category_'))
    app.add_handler(CallbackQueryHandler(recipe_button, pattern=r'recipe_'))
    app.add_handler(CallbackQueryHandler(weekly_menu, pattern=r'weekly_menu'))
    app.add_handler(CallbackQueryHandler(search_handler, pattern=r'search'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search))

    await app.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
