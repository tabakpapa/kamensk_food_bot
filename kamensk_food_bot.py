import os
import asyncio
import random
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("Не задан BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

PLACES = {
    "🍔 Бургеры": [
        {
            "name": "Бургер Кинг",
            "address": "просп. Победы, 65",
            "hours": "Уточняй в картах",
            "rating": "4.6",
            "desc": "Сетевые бургеры, комбо и напитки.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Бургер Кинг проспект Победы 65",
        },
        {
            "name": "Rostic's",
            "address": "просп. Победы, 65",
            "hours": "Уточняй в картах",
            "rating": "4.5",
            "desc": "Курица, бургеры, баскеты и комбо.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Rostic's проспект Победы 65",
        },
    ],
    "🌯 Шаурма": [
        {
            "name": "Шаурма Маркет",
            "address": "ул. Ленина, 13А",
            "hours": "Уточняй в картах",
            "rating": "4.6",
            "desc": "Классическая шаурма и напитки.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Шаурма Маркет Ленина 13А",
        },
    ],
    "🍕 Пицца": [
        {
            "name": "Додо Пицца",
            "address": "Каменская ул., 91",
            "hours": "Уточняй в картах",
            "rating": "4.7",
            "desc": "Пицца, закуски, десерты и доставка.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Додо Пицца Каменская 91",
        },
    ],
    "☕ Кофе": [
        {
            "name": "Dozacoffee",
            "address": "Алюминиевая ул., 45",
            "hours": "С 08:00",
            "rating": "5.0",
            "desc": "Кофе, десерты и спокойная кофейня.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Dozacoffee Алюминиевая 45",
        },
    ],
    "🍺 Бары": [
        {
            "name": "Хрущёвка",
            "address": "Каменская ул., 12",
            "hours": "Уточняй в картах",
            "rating": "4.9",
            "desc": "Бар для вечерних встреч.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Хрущёвка Каменская 12",
        },
    ],
}

TOP_PLACES = ["Dozacoffee", "Хрущёвка", "Додо Пицца", "Бургер Кинг"]
NIGHT_PLACES = ["Хрущёвка"]

menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🍔 Бургеры"), KeyboardButton(text="🌯 Шаурма")],
        [KeyboardButton(text="🍕 Пицца"), KeyboardButton(text="☕ Кофе")],
        [KeyboardButton(text="🍺 Бары"), KeyboardButton(text="⭐ Лучшие места")],
        [KeyboardButton(text="🌙 Где поесть ночью"), KeyboardButton(text="🎲 Случайное место")],
        [KeyboardButton(text="ℹ️ Помощь")],
    ],
    resize_keyboard=True,
)

def card_buttons(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📍 Открыть в Яндекс Картах", url=url)]
        ]
    )

def all_places_list():
    result = []
    for items in PLACES.values():
        result.extend(items)
    return result

def find_place_by_name(name: str):
    for place in all_places_list():
        if place["name"] == name:
            return place
    return None

def format_place(place: dict) -> str:
    return (
        f"<b>{place['name']}</b>\n"
        f"📍 {place['address']}\n"
        f"⏰ {place['hours']}\n"
        f"⭐ {place['rating']}\n"
        f"📝 {place['desc']}"
    )

@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "🍴 Где поесть в Каменске\n\nВыбери категорию:",
        reply_markup=menu
    )
 @dp.message(F.text == "ℹ️ Помощь")
@dp.message(F.text == "/help")
async def help_handler(message: Message):
    await message.answer(
        "Что умеет бот:\n\n"
        "• показывает заведения по категориям\n"
        "• открывает заведения в Яндекс Картах\n"
        "• показывает лучшие места\n"
        "• показывает места, где можно поесть ночью\n"
        "• выбирает случайное место\n\n"
        "Команды:\n"
        "/start — открыть меню\n"
        "/help — помощь"
    )

@dp.message(F.text.in_(PLACES.keys()))
async def category_handler(message: Message):
    category = message.text
    await message.answer(f"{category} в Каменске-Уральском:")

    for place in PLACES[category]:
        await message.answer(
            format_place(place),
            parse_mode="HTML",
            reply_markup=card_buttons(place["url"]),
        )

@dp.message(F.text == "⭐ Лучшие места")
async def top_handler(message: Message):
    await message.answer("⭐ Лучшие места в Каменске-Уральском:")

    for name in TOP_PLACES:
        place = find_place_by_name(name)
        if place:
            await message.answer(
                format_place(place),
                parse_mode="HTML",
                reply_markup=card_buttons(place["url"]),
            )

@dp.message(F.text == "🌙 Где поесть ночью")
async def night_handler(message: Message):
    await message.answer("🌙 Места, которые часто работают допоздна:")

    for name in NIGHT_PLACES:
        place = find_place_by_name(name)
        if place:
            await message.answer(
                format_place(place),
                parse_mode="HTML",
                reply_markup=card_buttons(place["url"]),
            )

@dp.message(F.text == "🎲 Случайное место")
async def random_handler(message: Message):
    place = random.choice(all_places_list())
    await message.answer("🎲 Сегодня попробуй:")
    await message.answer(
        format_place(place),
        parse_mode="HTML",
        reply_markup=card_buttons(place["url"]),
    )

@dp.message()
async def fallback_handler(message: Message):
    await message.answer("Нажми /start и выбери кнопку из меню.")

async def main():
    me = await bot.get_me()
    print(f"BOT STARTED: @{me.username}", flush=True)
    await bot.delete_webhook(drop_pending_updates=True)
    print("WEBHOOK CLEARED", flush=True)
    print("POLLING", flush=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
