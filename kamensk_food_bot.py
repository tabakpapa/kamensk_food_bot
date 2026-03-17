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
    CallbackQuery,
)

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("Не задан BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# user_id -> list of place dict
FAVORITES = {}
RATINGS = {}
USER_VOTES = {}

PLACES = {
    "🍔 Бургеры": [
        {
            "id": "burger_1",
            "name": "Бургер Кинг",
            "address": "просп. Победы, 65",
            "hours": "Уточняй в картах",
            "rating": "4.6",
            "desc": "Сетевые бургеры, комбо и напитки.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Бургер Кинг проспект Победы 65",
        },
        {
            "id": "burger_2",
            "name": "Rostic's",
            "address": "ул. Суворова, 24",
            "hours": "До 00:00",
            "rating": "4.2",
            "desc": "Курица, бургеры, баскеты и комбо.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Rostic's Суворова 24",
        },
        {
            "id": "burger_3",
            "name": "Шампурико",
            "address": "Алюминиевая ул., 77Б",
            "hours": "С 10:30",
            "rating": "4.9",
            "desc": "Стритфуд, мясо и блюда на гриле.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Шампурико Алюминиевая 77Б",
        },
        {
            "id": "burger_4",
            "name": "Седьмое небо",
            "address": "Каменская ул., 79Б",
            "hours": "Уточняй в картах",
            "rating": "4.7",
            "desc": "Стритфуд, бургеры, шаурма и пицца.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Седьмое небо Каменская 79Б",
        },
        {
            "id": "burger_5",
            "name": "Subjoy",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.2",
            "desc": "Сэндвичи, бургеры и быстрый перекус.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Subjoy",
        },
        {
            "id": "burger_6",
            "name": "Русская забава",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.4",
            "desc": "Фастфуд и закуски.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Русская забава",
        },
    ],
    "🌯 Шаурма": [
        {
            "id": "shawarma_1",
            "name": "Шаурма Маркет",
            "address": "ул. Ленина, 13А",
            "hours": "Уточняй в картах",
            "rating": "4.6",
            "desc": "Классическая шаурма и напитки.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Шаурма Маркет Ленина 13А",
        },
        {
            "id": "shawarma_2",
            "name": "Лаваш",
            "address": "Алюминиевая ул., 78",
            "hours": "С 09:00",
            "rating": "4.5",
            "desc": "Шаверма, хот-доги и быстрые закуски.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Лаваш Алюминиевая 78",
        },
        {
            "id": "shawarma_3",
            "name": "Мясной Батя",
            "address": "просп. Победы, 75Б",
            "hours": "С 10:00",
            "rating": "4.3",
            "desc": "Шаурма и мясо на гриле.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Мясной Батя проспект Победы 75Б",
        },
        {
            "id": "shawarma_4",
            "name": "По шаурме",
            "address": "просп. Победы, 19",
            "hours": "Уточняй в картах",
            "rating": "Нет данных",
            "desc": "Шаурма и быстрый перекус.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский По шаурме проспект Победы 19",
        },
        {
            "id": "shawarma_5",
            "name": "Шаурма",
            "address": "Каменская ул., 82Б",
            "hours": "С 09:00",
            "rating": "4.6",
            "desc": "Точка с классической шаурмой.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Шаурма Каменская 82Б",
        },
        {
            "id": "shawarma_6",
            "name": "Шаурма восточная",
            "address": "ул. Бугарева, 3",
            "hours": "Уточняй в картах",
            "rating": "Нет данных",
            "desc": "Восточная шаурма и закуски.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Шаурма восточная Бугарева 3",
        },
        {
            "id": "shawarma_7",
            "name": "Мангал",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.7",
            "desc": "Шаурма, мясо и блюда на мангале.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Мангал",
        },
        {
            "id": "shawarma_8",
            "name": "Седьмое небо",
            "address": "Каменская ул., 79Б",
            "hours": "Уточняй в картах",
            "rating": "4.7",
            "desc": "Шаурма, бургеры и пицца.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Седьмое небо Каменская 79Б",
        },
        {
            "id": "shawarma_9",
            "name": "Шампурико",
            "address": "Алюминиевая ул., 77Б",
            "hours": "С 10:30",
            "rating": "4.9",
            "desc": "Шаурма и блюда на гриле.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Шампурико Алюминиевая 77Б",
        },
    ],
    "🍕 Пицца": [
        {
            "id": "pizza_1",
            "name": "Додо Пицца",
            "address": "Каменская ул., 91",
            "hours": "Уточняй в картах",
            "rating": "4.7",
            "desc": "Пицца, закуски, десерты и доставка.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Додо Пицца Каменская 91",
        },
        {
            "id": "pizza_2",
            "name": "Додо Пицца",
            "address": "просп. Победы, 44",
            "hours": "Уточняй в картах",
            "rating": "4.8",
            "desc": "Ещё одна точка Додо Пиццы.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Додо Пицца проспект Победы 44",
        },
        {
            "id": "pizza_3",
            "name": "Pizza Mia",
            "address": "ул. Суворова, 18",
            "hours": "С 11:00",
            "rating": "4.5",
            "desc": "Пицца и быстрые обеды.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Pizza Mia Суворова 18",
        },
        {
            "id": "pizza_4",
            "name": "Pizza Mia",
            "address": "просп. Победы, 51А",
            "hours": "С 11:00",
            "rating": "4.2",
            "desc": "Пицца, закуски и семейный формат.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Pizza Mia проспект Победы 51А",
        },
        {
            "id": "pizza_5",
            "name": "Италиан Пицца",
            "address": "ул. Суворова, 23А",
            "hours": "С 09:00",
            "rating": "4.9",
            "desc": "Пицца и итальянское меню.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Италиан Пицца Суворова 23А",
        },
        {
            "id": "pizza_6",
            "name": "Италиан Пицца",
            "address": "просп. Победы, 44",
            "hours": "Уточняй в картах",
            "rating": "4.9",
            "desc": "Ещё одна точка Италиан Пиццы.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Италиан Пицца проспект Победы 44",
        },
        {
            "id": "pizza_7",
            "name": "Pizzatime",
            "address": "Каменская ул., 12",
            "hours": "С 12:00",
            "rating": "Нет данных",
            "desc": "Пицца и быстрый перекус.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Pizzatime Каменская 12",
        },
        {
            "id": "pizza_8",
            "name": "Sushkof i Pizza",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.5",
            "desc": "Пицца, роллы и доставка.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Sushkof i Pizza",
        },
        {
            "id": "pizza_9",
            "name": "Большие тарелки",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.3",
            "desc": "Пицца, горячие блюда и кафе-формат.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Большие тарелки",
        },
        {
            "id": "pizza_10",
            "name": "Седьмое небо",
            "address": "Каменская ул., 79Б",
            "hours": "Уточняй в картах",
            "rating": "4.7",
            "desc": "Стритфуд, шаурма и пицца.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Седьмое небо Каменская 79Б",
        },
    ],
    "☕ Кофе": [
        {
            "id": "coffee_1",
            "name": "Dozacoffee",
            "address": "Алюминиевая ул., 45",
            "hours": "До 21:00",
            "rating": "5.0",
            "desc": "Кофе, десерты и спокойная кофейня.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Dozacoffee Алюминиевая 45",
        },
        {
            "id": "coffee_2",
            "name": "Черный лис",
            "address": "просп. Победы, 6",
            "hours": "Уточняй в картах",
            "rating": "4.5",
            "desc": "Кофе с собой и десерты.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Черный лис проспект Победы 6",
        },
        {
            "id": "coffee_3",
            "name": "Черный лис",
            "address": "Алюминиевая ул., 68",
            "hours": "Уточняй в картах",
            "rating": "4.5",
            "desc": "Ещё одна точка кофейни Черный лис.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Черный лис Алюминиевая 68",
        },
        {
            "id": "coffee_4",
            "name": "Coffee Print",
            "address": "просп. Победы, 65",
            "hours": "С 10:00",
            "rating": "5.0",
            "desc": "Кофе, выпечка и перекус.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Coffee Print проспект Победы 65",
        },
        {
            "id": "coffee_5",
            "name": "По любви",
            "address": "Алюминиевая ул., 37",
            "hours": "Уточняй в картах",
            "rating": "4.4",
            "desc": "Кофейня и десерты.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский По любви Алюминиевая 37",
        },
        {
            "id": "coffee_6",
            "name": "Это твой кофе",
            "address": "ул. Суворова, 24",
            "hours": "Уточняй в картах",
            "rating": "Нет данных",
            "desc": "Кофе с собой.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Это твой кофе Суворова 24",
        },
        {
            "id": "coffee_7",
            "name": "Bubble Cafe",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.5",
            "desc": "Напитки, десерты и кафе-формат.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Bubble Cafe",
        },
        {
            "id": "coffee_8",
            "name": "Avokado Gold",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.4",
            "desc": "Кафе и кофейные напитки.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Avokado Gold",
        },
        {
            "id": "coffee_9",
            "name": "На Берегу",
            "address": "Набережная ул., 9",
            "hours": "Уточняй в картах",
            "rating": "4.4",
            "desc": "Кофе и спокойное место.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский На Берегу Набережная 9",
        },
    ],
    "🍺 Бары": [
        {
            "id": "bar_1",
            "name": "Хрущёвка",
            "address": "Каменская ул., 12",
            "hours": "Уточняй в картах",
            "rating": "4.9",
            "desc": "Бар для вечерних встреч.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Хрущёвка Каменская 12",
        },
        {
            "id": "bar_2",
            "name": "Моджо",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.5",
            "desc": "Бар с вечерней атмосферой.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Моджо",
        },
        {
            "id": "bar_3",
            "name": "K1",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.6",
            "desc": "Бар и место для вечернего отдыха.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский K1",
        },
        {
            "id": "bar_4",
            "name": "Генрих и Генриетта",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.4",
            "desc": "Бар / паб-формат.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Генрих и Генриетта",
        },
        {
            "id": "bar_5",
            "name": "Шахта",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.3",
            "desc": "Бар и вечерний отдых.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Шахта",
        },
        {
            "id": "bar_6",
            "name": "Роял Рум",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.0",
            "desc": "Бар и клубный формат.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Роял Рум",
        },
        {
            "id": "bar_7",
            "name": "Седьмое небо",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "Нет данных",
            "desc": "Бар / кафе-формат.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Седьмое небо бар",
        },
    ],
}

TOP_PLACES = [
    "Dozacoffee",
    "Италиан Пицца",
    "Хрущёвка",
    "Шампурико",
    "Додо Пицца",
    "Бургер Кинг",
]

NIGHT_PLACES = [
    "Хрущёвка",
    "Моджо",
    "K1",
    "Роял Рум",
    "Генрих и Генриетта",
    "Седьмое небо",
]

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍔 Бургеры"), KeyboardButton(text="🌯 Шаурма")],
            [KeyboardButton(text="🍕 Пицца"), KeyboardButton(text="☕ Кофе")],
            [KeyboardButton(text="🍺 Бары"), KeyboardButton(text="⭐ Лучшие места")],
            [KeyboardButton(text="🌙 Где поесть ночью"), KeyboardButton(text="🎲 Случайное место")],
            [KeyboardButton(text="❤️ Моё избранное")],
            [KeyboardButton(text="🧠 Подобрать место")],
            [KeyboardButton(text="ℹ️ Помощь")],
        ],
        resize_keyboard=True
    )

def get_back_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )
    
def get_smart_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💸 Дёшево"), KeyboardButton(text="⚡ Быстро")],
            [KeyboardButton(text="☕ Посидеть"), KeyboardButton(text="🌙 Ночью")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True
    )
    
def get_place_score(place_id: str):
    data = RATINGS.get(place_id, {"up": 0, "down": 0})
    return data["up"], data["down"]

def card_buttons(place: dict) -> InlineKeyboardMarkup:
    up, down = get_place_score(place["id"])

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📍 Открыть в Яндекс Картах", url=place["url"])],
            [InlineKeyboardButton(text="❤️ В избранное", callback_data=f"fav:{place['id']}")],
            [
                InlineKeyboardButton(text=f"👍 {up}", callback_data=f"like:{place['id']}"),
                InlineKeyboardButton(text=f"👎 {down}", callback_data=f"dislike:{place['id']}"),
            ],
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

def find_place_by_id(place_id: str):
    for place in all_places_list():
        if place["id"] == place_id:
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
    
@dp.message(F.text == "🧠 Подобрать место")
async def smart_menu_handler(message: Message):
    await message.answer(
        "Выбери, что ты хочешь:",
        reply_markup=get_smart_keyboard()
    )

@dp.message(F.text == "💸 Дёшево")
async def cheap_handler(message: Message):
    places = all_places_list()

    # просто берём случайные (пока без цен)
    selected = random.sample(places, min(5, len(places)))

    await message.answer("💸 Недорогие варианты:")

    for place in selected:
        await message.answer(
            format_place(place),
            parse_mode="HTML",
            reply_markup=card_buttons(place),
        )


@dp.message(F.text == "⚡ Быстро")
async def fast_handler(message: Message):
    fast_categories = ["🍔 Бургеры", "🌯 Шаурма"]

    result = []
    for cat in fast_categories:
        result.extend(PLACES.get(cat, []))

    selected = random.sample(result, min(5, len(result)))

    await message.answer("⚡ Быстрый перекус:")

    for place in selected:
        await message.answer(
            format_place(place),
            parse_mode="HTML",
            reply_markup=card_buttons(place),
        )


@dp.message(F.text == "☕ Посидеть")
async def chill_handler(message: Message):
    places = PLACES.get("☕ Кофе", [])

    await message.answer("☕ Места для посидеть:")

    for place in places:
        await message.answer(
            format_place(place),
            parse_mode="HTML",
            reply_markup=card_buttons(place),
        )


@dp.message(F.text == "🌙 Ночью")
async def night_smart_handler(message: Message):
    await message.answer("🌙 Где поесть ночью:")

    for name in NIGHT_PLACES:
        place = find_place_by_name(name)
        if place:
            await message.answer(
                format_place(place),
                parse_mode="HTML",
                reply_markup=card_buttons(place),
            )
            
@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "🍴 Где поесть в Каменске\n\nВыбери категорию:",
        reply_markup=get_main_keyboard()
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
        "• выбирает случайное место\n"
        "• умеет сохранять места в избранное\n\n"
        "Команды:\n"
        "/start — открыть меню\n"
        "/help — помощь"
    )

@dp.message(F.text.in_(PLACES.keys()))
async def category_handler(message: Message):
    category = message.text

    await message.answer(
        f"{category} в Каменске-Уральском:",
        reply_markup=get_back_keyboard()
    )

    for place in PLACES[category]:
        await message.answer(
            format_place(place),
            parse_mode="HTML",
            reply_markup=card_buttons(place),
        )

@dp.message(F.text == "⭐ Лучшие места")
async def top_handler(message: Message):
    all_places = all_places_list()

    # сортируем по лайкам
    sorted_places = sorted(
        all_places,
        key=lambda p: RATINGS.get(p["id"], {"up": 0})["up"],
        reverse=True
    )

    top_places = sorted_places[:10]  # топ 10

    await message.answer(
        "⭐ Топ заведений по мнению пользователей:",
        reply_markup=get_back_keyboard()
    )

    if not top_places:
        await message.answer("Пока нет оценок.")
        return

    for place in top_places:
        await message.answer(
            format_place(place),
            parse_mode="HTML",
            reply_markup=card_buttons(place),
        )
    await message.answer(
        "⭐ Лучшие места в Каменске-Уральском:",
        reply_markup=get_back_keyboard()
    )

    for name in TOP_PLACES:
        place = find_place_by_name(name)
        if place:
            await message.answer(
                format_place(place),
                parse_mode="HTML",
                reply_markup=card_buttons(place),
            )

@dp.message(F.text == "🌙 Где поесть ночью")
async def night_handler(message: Message):
    await message.answer(
        "🌙 Места, которые часто работают допоздна:",
        reply_markup=get_back_keyboard()
    )

    for name in NIGHT_PLACES:
        place = find_place_by_name(name)
        if place:
            await message.answer(
                format_place(place),
                parse_mode="HTML",
                reply_markup=card_buttons(place),
            )

@dp.message(F.text == "🎲 Случайное место")
async def random_handler(message: Message):
    place = random.choice(all_places_list())
    await message.answer(
        "🎲 Сегодня попробуй:",
        reply_markup=get_back_keyboard()
    )
    await message.answer(
        format_place(place),
        parse_mode="HTML",
        reply_markup=card_buttons(place),
    )

@dp.message(F.text == "❤️ Моё избранное")
async def favorites_handler(message: Message):
    user_id = message.from_user.id
    user_favorites = FAVORITES.get(user_id, [])

    if not user_favorites:
        await message.answer(
            "У тебя пока нет избранных мест.",
            reply_markup=get_back_keyboard()
        )
        return

    await message.answer(
        "❤️ Твоё избранное:",
        reply_markup=get_back_keyboard()
    )

    for place in user_favorites:
        await message.answer(
            format_place(place),
            parse_mode="HTML",
            reply_markup=card_buttons(place),
        )

@dp.callback_query(F.data.startswith("fav:"))
async def add_to_favorites_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    place_id = callback.data.split(":", 1)[1]
    place = find_place_by_id(place_id)

    if not place:
        await callback.answer("Место не найдено", show_alert=True)
        return

    if user_id not in FAVORITES:
        FAVORITES[user_id] = []

    already_added = any(saved_place["id"] == place["id"] for saved_place in FAVORITES[user_id])

    if already_added:
        await callback.answer("Уже в избранном ❤️", show_alert=False)
        return

    FAVORITES[user_id].append(place)
    await callback.answer("Добавлено в избранное ❤️", show_alert=False)


@dp.callback_query(F.data.startswith("like:"))
async def like_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    place_id = callback.data.split(":", 1)[1]
    place = find_place_by_id(place_id)

    if not place:
        await callback.answer("Место не найдено", show_alert=True)
        return

    if place_id not in RATINGS:
        RATINGS[place_id] = {"up": 0, "down": 0}

    if user_id not in USER_VOTES:
        USER_VOTES[user_id] = {}

    current_vote = USER_VOTES[user_id].get(place_id)

    if current_vote == "like":
        await callback.answer("Ты уже поставил 👍")
        return

    if current_vote == "dislike":
        RATINGS[place_id]["down"] -= 1

    RATINGS[place_id]["up"] += 1
    USER_VOTES[user_id][place_id] = "like"

    await callback.message.edit_reply_markup(
        reply_markup=card_buttons(place)
    )
    await callback.answer("Ты поставил 👍")


@dp.callback_query(F.data.startswith("dislike:"))
async def dislike_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    place_id = callback.data.split(":", 1)[1]
    place = find_place_by_id(place_id)

    if not place:
        await callback.answer("Место не найдено", show_alert=True)
        return

    if place_id not in RATINGS:
        RATINGS[place_id] = {"up": 0, "down": 0}

    if user_id not in USER_VOTES:
        USER_VOTES[user_id] = {}

    current_vote = USER_VOTES[user_id].get(place_id)

    if current_vote == "dislike":
        await callback.answer("Ты уже поставил 👎")
        return

    if current_vote == "like":
        RATINGS[place_id]["up"] -= 1

    RATINGS[place_id]["down"] += 1
    USER_VOTES[user_id][place_id] = "dislike"

    await callback.message.edit_reply_markup(
        reply_markup=card_buttons(place)
    )
    await callback.answer("Ты поставил 👎")


@dp.message(F.text == "⬅️ Назад")
async def back_handler(message: Message):
    await message.answer(
        "🍴 Снова главное меню\n\nВыбери категорию:",
        reply_markup=get_main_keyboard()
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
