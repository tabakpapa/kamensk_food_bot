import os
import asyncio
import random
import sqlite3
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("Не задан BOT_TOKEN")

ADMIN_ID = int(os.getenv("ADMIN_ID", "729024995"))
DB_PATH = os.getenv("DB_PATH", "bot.db")

bot = Bot(token=TOKEN)
dp = Dispatcher()

BOT_USERNAME: Optional[str] = None
SMART_STATE: dict[int, dict] = {}
USER_CONTEXT: dict[int, dict] = {}
ORDER_STATE: dict[int, dict] = {}

ADS = [
    "📢 <b>Реклама</b>\n\nХочешь продвинуть своё заведение в боте? Напиши администратору.",
    "📢 <b>Реклама</b>\n\nПартнёрские места получают приоритет в подборках и отдельные промо-блоки.",
    "📢 <b>Реклама</b>\n\nЭтот бот можно использовать как городской food-гид. Для размещения — свяжись с владельцем.",
]

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
            "is_partner": False,
            "budget": "💸 До 500",
            "formats": ["👤 Один", "👥 Компания"],
            "food_type": "🍔 Бургеры",
            "distance": "🚕 Не важно",
            "night": True,
        },
        {
            "id": "burger_2",
            "name": "Rostic's",
            "address": "ул. Суворова, 24",
            "hours": "До 00:00",
            "rating": "4.2",
            "desc": "Курица, бургеры, баскеты и комбо.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Rostic's Суворова 24",
            "is_partner": False,
            "budget": "💸 До 500",
            "formats": ["👤 Один", "👥 Компания"],
            "food_type": "🍔 Бургеры",
            "distance": "🚕 Не важно",
            "night": True,
        },
        {
            "id": "burger_3",
            "name": "Шампурико",
            "address": "Алюминиевая ул., 77Б",
            "hours": "С 10:30",
            "rating": "4.9",
            "desc": "Стритфуд, мясо и блюда на гриле.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Шампурико Алюминиевая 77Б",
            "is_partner": True,
            "budget": "💰 До 1000",
            "formats": ["👤 Один", "👥 Компания"],
            "food_type": "🍔 Бургеры",
            "distance": "🚕 Не важно",
            "night": False,
        },
        {
            "id": "burger_4",
            "name": "Седьмое небо",
            "address": "Каменская ул., 79Б",
            "hours": "Уточняй в картах",
            "rating": "4.7",
            "desc": "Стритфуд, бургеры, шаурма и пицца.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Седьмое небо Каменская 79Б",
            "is_partner": True,
            "budget": "💰 До 1000",
            "formats": ["👤 Один", "💑 Свидание", "👥 Компания"],
            "food_type": "🍔 Бургеры",
            "distance": "🚶 Рядом",
            "night": True,
        },
        {
            "id": "burger_5",
            "name": "Subjoy",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.2",
            "desc": "Сэндвичи, бургеры и быстрый перекус.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Subjoy",
            "is_partner": False,
            "budget": "💸 До 500",
            "formats": ["👤 Один"],
            "food_type": "🍔 Бургеры",
            "distance": "🚶 Рядом",
            "night": False,
        },
        {
            "id": "burger_6",
            "name": "Русская забава",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.4",
            "desc": "Фастфуд и закуски.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Русская забава",
            "is_partner": False,
            "budget": "💸 До 500",
            "formats": ["👤 Один"],
            "food_type": "🍔 Бургеры",
            "distance": "🚕 Не важно",
            "night": False,
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
            "is_partner": True,
            "budget": "💸 До 500",
            "formats": ["👤 Один", "👥 Компания"],
            "food_type": "🌯 Шаурма",
            "distance": "🚶 Рядом",
            "night": False,
        },
        {
            "id": "shawarma_2",
            "name": "Лаваш",
            "address": "Алюминиевая ул., 78",
            "hours": "С 09:00",
            "rating": "4.5",
            "desc": "Шаверма, хот-доги и быстрые закуски.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Лаваш Алюминиевая 78",
            "is_partner": False,
            "budget": "💸 До 500",
            "formats": ["👤 Один"],
            "food_type": "🌯 Шаурма",
            "distance": "🚶 Рядом",
            "night": False,
        },
        {
            "id": "shawarma_3",
            "name": "Мясной Батя",
            "address": "просп. Победы, 75Б",
            "hours": "С 10:00",
            "rating": "4.3",
            "desc": "Шаурма и мясо на гриле.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Мясной Батя проспект Победы 75Б",
            "is_partner": False,
            "budget": "💸 До 500",
            "formats": ["👤 Один", "👥 Компания"],
            "food_type": "🌯 Шаурма",
            "distance": "🚕 Не важно",
            "night": False,
        },
        {
            "id": "shawarma_4",
            "name": "По шаурме",
            "address": "просп. Победы, 19",
            "hours": "Уточняй в картах",
            "rating": "Нет данных",
            "desc": "Шаурма и быстрый перекус.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский По шаурме проспект Победы 19",
            "is_partner": False,
            "budget": "💸 До 500",
            "formats": ["👤 Один"],
            "food_type": "🌯 Шаурма",
            "distance": "🚶 Рядом",
            "night": False,
        },
        {
            "id": "shawarma_5",
            "name": "Шаурма",
            "address": "Каменская ул., 82Б",
            "hours": "С 09:00",
            "rating": "4.6",
            "desc": "Точка с классической шаурмой.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Шаурма Каменская 82Б",
            "is_partner": False,
            "budget": "💸 До 500",
            "formats": ["👤 Один"],
            "food_type": "🌯 Шаурма",
            "distance": "🚶 Рядом",
            "night": False,
        },
        {
            "id": "shawarma_6",
            "name": "Шаурма восточная",
            "address": "ул. Бугарева, 3",
            "hours": "Уточняй в картах",
            "rating": "Нет данных",
            "desc": "Восточная шаурма и закуски.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Шаурма восточная Бугарева 3",
            "is_partner": False,
            "budget": "💸 До 500",
            "formats": ["👤 Один"],
            "food_type": "🌯 Шаурма",
            "distance": "🚕 Не важно",
            "night": False,
        },
        {
            "id": "shawarma_7",
            "name": "Мангал",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.7",
            "desc": "Шаурма, мясо и блюда на мангале.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Мангал",
            "is_partner": False,
            "budget": "💰 До 1000",
            "formats": ["👤 Один", "👥 Компания"],
            "food_type": "🌯 Шаурма",
            "distance": "🚕 Не важно",
            "night": False,
        },
        {
            "id": "shawarma_8",
            "name": "Седьмое небо",
            "address": "Каменская ул., 79Б",
            "hours": "Уточняй в картах",
            "rating": "4.7",
            "desc": "Шаурма, бургеры и пицца.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Седьмое небо Каменская 79Б",
            "is_partner": True,
            "budget": "💰 До 1000",
            "formats": ["👤 Один", "💑 Свидание", "👥 Компания"],
            "food_type": "🌯 Шаурма",
            "distance": "🚶 Рядом",
            "night": True,
        },
        {
            "id": "shawarma_9",
            "name": "Шампурико",
            "address": "Алюминиевая ул., 77Б",
            "hours": "С 10:30",
            "rating": "4.9",
            "desc": "Шаурма и блюда на гриле.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Шампурико Алюминиевая 77Б",
            "is_partner": True,
            "budget": "💰 До 1000",
            "formats": ["👤 Один", "👥 Компания"],
            "food_type": "🌯 Шаурма",
            "distance": "🚕 Не важно",
            "night": False,
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
            "is_partner": False,
            "budget": "💰 До 1000",
            "formats": ["💑 Свидание", "👥 Компания"],
            "food_type": "🍕 Пицца",
            "distance": "🚕 Не важно",
            "night": False,
        },
        {
            "id": "pizza_2",
            "name": "Додо Пицца",
            "address": "просп. Победы, 44",
            "hours": "Уточняй в картах",
            "rating": "4.8",
            "desc": "Ещё одна точка Додо Пиццы.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Додо Пицца проспект Победы 44",
            "is_partner": False,
            "budget": "💰 До 1000",
            "formats": ["💑 Свидание", "👥 Компания"],
            "food_type": "🍕 Пицца",
            "distance": "🚕 Не важно",
            "night": False,
        },
        {
            "id": "pizza_3",
            "name": "Pizza Mia",
            "address": "ул. Суворова, 18",
            "hours": "С 11:00",
            "rating": "4.5",
            "desc": "Пицца и быстрые обеды.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Pizza Mia Суворова 18",
            "is_partner": False,
            "budget": "💰 До 1000",
            "formats": ["👤 Один", "👥 Компания"],
            "food_type": "🍕 Пицца",
            "distance": "🚕 Не важно",
            "night": False,
        },
        {
            "id": "pizza_4",
            "name": "Pizza Mia",
            "address": "просп. Победы, 51А",
            "hours": "С 11:00",
            "rating": "4.2",
            "desc": "Пицца, закуски и семейный формат.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Pizza Mia проспект Победы 51А",
            "is_partner": False,
            "budget": "💰 До 1000",
            "formats": ["👤 Один", "👥 Компания"],
            "food_type": "🍕 Пицца",
            "distance": "🚕 Не важно",
            "night": False,
        },
        {
            "id": "pizza_5",
            "name": "Италиан Пицца",
            "address": "ул. Суворова, 23А",
            "hours": "С 09:00",
            "rating": "4.9",
            "desc": "Пицца и итальянское меню.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Италиан Пицца Суворова 23А",
            "is_partner": True,
            "budget": "💰 До 1000",
            "formats": ["💑 Свидание", "👥 Компания"],
            "food_type": "🍕 Пицца",
            "distance": "🚶 Рядом",
            "night": False,
        },
        {
            "id": "pizza_6",
            "name": "Италиан Пицца",
            "address": "просп. Победы, 44",
            "hours": "Уточняй в картах",
            "rating": "4.9",
            "desc": "Ещё одна точка Италиан Пиццы.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Италиан Пицца проспект Победы 44",
            "is_partner": True,
            "budget": "💰 До 1000",
            "formats": ["💑 Свидание", "👥 Компания"],
            "food_type": "🍕 Пицца",
            "distance": "🚕 Не важно",
            "night": False,
        },
        {
            "id": "pizza_7",
            "name": "Pizzatime",
            "address": "Каменская ул., 12",
            "hours": "С 12:00",
            "rating": "Нет данных",
            "desc": "Пицца и быстрый перекус.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Pizzatime Каменская 12",
            "is_partner": False,
            "budget": "💰 До 1000",
            "formats": ["👤 Один"],
            "food_type": "🍕 Пицца",
            "distance": "🚶 Рядом",
            "night": False,
        },
        {
            "id": "pizza_8",
            "name": "Sushkof i Pizza",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.5",
            "desc": "Пицца, роллы и доставка.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Sushkof i Pizza",
            "is_partner": False,
            "budget": "💰 До 1000",
            "formats": ["💑 Свидание", "👥 Компания"],
            "food_type": "🍕 Пицца",
            "distance": "🚕 Не важно",
            "night": False,
        },
        {
            "id": "pizza_9",
            "name": "Большие тарелки",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.3",
            "desc": "Пицца, горячие блюда и кафе-формат.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Большие тарелки",
            "is_partner": False,
            "budget": "💰 До 1000",
            "formats": ["💑 Свидание", "👥 Компания"],
            "food_type": "🍕 Пицца",
            "distance": "🚕 Не важно",
            "night": False,
        },
        {
            "id": "pizza_10",
            "name": "Седьмое небо",
            "address": "Каменская ул., 79Б",
            "hours": "Уточняй в картах",
            "rating": "4.7",
            "desc": "Стритфуд, шаурма и пицца.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Седьмое небо Каменская 79Б",
            "is_partner": True,
            "budget": "💰 До 1000",
            "formats": ["💑 Свидание", "👥 Компания"],
            "food_type": "🍕 Пицца",
            "distance": "🚶 Рядом",
            "night": True,
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
            "is_partner": True,
            "budget": "💸 До 500",
            "formats": ["👤 Один", "💑 Свидание"],
            "food_type": "☕ Кофе",
            "distance": "🚶 Рядом",
            "night": False,
        },
        {
            "id": "coffee_2",
            "name": "Черный лис",
            "address": "просп. Победы, 6",
            "hours": "Уточняй в картах",
            "rating": "4.5",
            "desc": "Кофе с собой и десерты.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Черный лис проспект Победы 6",
            "is_partner": False,
            "budget": "💸 До 500",
            "formats": ["👤 Один", "💑 Свидание"],
            "food_type": "☕ Кофе",
            "distance": "🚶 Рядом",
            "night": False,
        },
        {
            "id": "coffee_3",
            "name": "Черный лис",
            "address": "Алюминиевая ул., 68",
            "hours": "Уточняй в картах",
            "rating": "4.5",
            "desc": "Ещё одна точка кофейни Черный лис.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Черный лис Алюминиевая 68",
            "is_partner": False,
            "budget": "💸 До 500",
            "formats": ["👤 Один", "💑 Свидание"],
            "food_type": "☕ Кофе",
            "distance": "🚶 Рядом",
            "night": False,
        },
        {
            "id": "coffee_4",
            "name": "Coffee Print",
            "address": "просп. Победы, 65",
            "hours": "С 10:00",
            "rating": "5.0",
            "desc": "Кофе, выпечка и перекус.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Coffee Print проспект Победы 65",
            "is_partner": False,
            "budget": "💸 До 500",
            "formats": ["👤 Один"],
            "food_type": "☕ Кофе",
            "distance": "🚶 Рядом",
            "night": False,
        },
        {
            "id": "coffee_5",
            "name": "По любви",
            "address": "Алюминиевая ул., 37",
            "hours": "Уточняй в картах",
            "rating": "4.4",
            "desc": "Кофейня и десерты.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский По любви Алюминиевая 37",
            "is_partner": False,
            "budget": "💸 До 500",
            "formats": ["💑 Свидание"],
            "food_type": "☕ Кофе",
            "distance": "🚶 Рядом",
            "night": False,
        },
        {
            "id": "coffee_6",
            "name": "Это твой кофе",
            "address": "ул. Суворова, 24",
            "hours": "Уточняй в картах",
            "rating": "Нет данных",
            "desc": "Кофе с собой.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Это твой кофе Суворова 24",
            "is_partner": False,
            "budget": "💸 До 500",
            "formats": ["👤 Один"],
            "food_type": "☕ Кофе",
            "distance": "🚶 Рядом",
            "night": False,
        },
        {
            "id": "coffee_7",
            "name": "Bubble Cafe",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.5",
            "desc": "Напитки, десерты и кафе-формат.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Bubble Cafe",
            "is_partner": False,
            "budget": "💸 До 500",
            "formats": ["💑 Свидание", "👥 Компания"],
            "food_type": "☕ Кофе",
            "distance": "🚕 Не важно",
            "night": False,
        },
        {
            "id": "coffee_8",
            "name": "Avokado Gold",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.4",
            "desc": "Кафе и кофейные напитки.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Avokado Gold",
            "is_partner": False,
            "budget": "💰 До 1000",
            "formats": ["💑 Свидание", "👥 Компания"],
            "food_type": "☕ Кофе",
            "distance": "🚕 Не важно",
            "night": False,
        },
        {
            "id": "coffee_9",
            "name": "На Берегу",
            "address": "Набережная ул., 9",
            "hours": "Уточняй в картах",
            "rating": "4.4",
            "desc": "Кофе и спокойное место.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский На Берегу Набережная 9",
            "is_partner": False,
            "budget": "💰 До 1000",
            "formats": ["💑 Свидание"],
            "food_type": "☕ Кофе",
            "distance": "🚕 Не важно",
            "night": False,
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
            "is_partner": True,
            "budget": "💰 До 1000",
            "formats": ["👥 Компания", "💑 Свидание"],
            "food_type": "🍺 Бары",
            "distance": "🚕 Не важно",
            "night": True,
        },
        {
            "id": "bar_2",
            "name": "Моджо",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.5",
            "desc": "Бар с вечерней атмосферой.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Моджо",
            "is_partner": False,
            "budget": "💰 До 1000",
            "formats": ["👥 Компания", "💑 Свидание"],
            "food_type": "🍺 Бары",
            "distance": "🚕 Не важно",
            "night": True,
        },
        {
            "id": "bar_3",
            "name": "K1",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.6",
            "desc": "Бар и место для вечернего отдыха.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский K1",
            "is_partner": False,
            "budget": "💰 До 1000",
            "formats": ["👥 Компания"],
            "food_type": "🍺 Бары",
            "distance": "🚕 Не важно",
            "night": True,
        },
        {
            "id": "bar_4",
            "name": "Генрих и Генриетта",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.4",
            "desc": "Бар / паб-формат.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Генрих и Генриетта",
            "is_partner": False,
            "budget": "💰 До 1000",
            "formats": ["💑 Свидание", "👥 Компания"],
            "food_type": "🍺 Бары",
            "distance": "🚕 Не важно",
            "night": True,
        },
        {
            "id": "bar_5",
            "name": "Шахта",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.3",
            "desc": "Бар и вечерний отдых.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Шахта",
            "is_partner": False,
            "budget": "💰 До 1000",
            "formats": ["👥 Компания"],
            "food_type": "🍺 Бары",
            "distance": "🚕 Не важно",
            "night": True,
        },
        {
            "id": "bar_6",
            "name": "Роял Рум",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.0",
            "desc": "Бар и клубный формат.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Роял Рум",
            "is_partner": False,
            "budget": "💰 До 1000",
            "formats": ["👥 Компания"],
            "food_type": "🍺 Бары",
            "distance": "🚕 Не важно",
            "night": True,
        },
        {
            "id": "bar_7",
            "name": "Седьмое небо",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "Нет данных",
            "desc": "Бар / кафе-формат.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Седьмое небо бар",
            "is_partner": True,
            "budget": "💰 До 1000",
            "formats": ["💑 Свидание", "👥 Компания"],
            "food_type": "🍺 Бары",
            "distance": "🚶 Рядом",
            "night": True,
        },
    ],
}


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            user_id INTEGER,
            place_id TEXT,
            PRIMARY KEY (user_id, place_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            user_id INTEGER,
            place_id TEXT,
            vote TEXT,
            PRIMARY KEY (user_id, place_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS partners (
            place_id TEXT PRIMARY KEY,
            is_partner INTEGER NOT NULL DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS analytics (
            metric TEXT PRIMARY KEY,
            value INTEGER NOT NULL DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            place_id TEXT,
            place_name TEXT,
            customer_name TEXT,
            phone TEXT,
            mode TEXT,
            address TEXT,
            items TEXT,
            comment TEXT,
            status TEXT DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def save_user(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()


def get_all_users() -> list[int]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users")
    rows = cur.fetchall()
    conn.close()
    return [row[0] for row in rows]


def add_favorite_db(user_id: int, place_id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO favorites (user_id, place_id) VALUES (?, ?)",
        (user_id, place_id)
    )
    conn.commit()
    conn.close()


def get_favorites_db(user_id: int) -> list[str]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT place_id FROM favorites WHERE user_id = ?", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return [row[0] for row in rows]


def get_vote_db(user_id: int, place_id: str) -> Optional[str]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT vote FROM votes WHERE user_id = ? AND place_id = ?",
        (user_id, place_id)
    )
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def set_vote_db(user_id: int, place_id: str, vote: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO votes (user_id, place_id, vote)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, place_id) DO UPDATE SET vote = excluded.vote
    """, (user_id, place_id, vote))
    conn.commit()
    conn.close()


def count_votes_db(place_id: str) -> tuple[int, int]:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM votes WHERE place_id = ? AND vote = 'like'",
        (place_id,)
    )
    up = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM votes WHERE place_id = ? AND vote = 'dislike'",
        (place_id,)
    )
    down = cur.fetchone()[0]

    conn.close()
    return up, down


def set_partner_db(place_id: str, is_partner: bool):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO partners (place_id, is_partner)
        VALUES (?, ?)
        ON CONFLICT(place_id) DO UPDATE SET is_partner = excluded.is_partner
    """, (place_id, 1 if is_partner else 0))
    conn.commit()
    conn.close()


def get_partners_map() -> dict[str, bool]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT place_id, is_partner FROM partners")
    rows = cur.fetchall()
    conn.close()
    return {place_id: bool(is_partner) for place_id, is_partner in rows}


def inc_metric(name: str, value: int = 1):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO analytics (metric, value)
        VALUES (?, ?)
        ON CONFLICT(metric) DO UPDATE SET value = value + excluded.value
    """, (name, value))
    conn.commit()
    conn.close()


def get_metric(name: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT value FROM analytics WHERE metric = ?", (name,))
    row = cur.fetchone()
    conn.close()
    return int(row[0]) if row else 0


def get_metrics_map() -> dict[str, int]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT metric, value FROM analytics")
    rows = cur.fetchall()
    conn.close()
    return {metric: int(value) for metric, value in rows}


def save_order_db(data: dict):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO orders (
            user_id, place_id, place_name, customer_name, phone,
            mode, address, items, comment, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'new')
    """, (
        data["user_id"],
        data["place_id"],
        data["place_name"],
        data["customer_name"],
        data["phone"],
        data["mode"],
        data.get("address", "Самовывоз"),
        data["items"],
        data["comment"],
    ))
    conn.commit()
    conn.close()


def get_recent_orders(limit: int = 10) -> list[tuple]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, place_name, customer_name, phone, status, created_at
        FROM orders
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows


def all_places_list() -> list[dict]:
    result = []
    for items in PLACES.values():
        result.extend(items)
    return result


def find_place_by_id(place_id: str) -> Optional[dict]:
    for place in all_places_list():
        if place["id"] == place_id:
            return place
    return None


def get_place_category(place_id: str) -> Optional[str]:
    for category, items in PLACES.items():
        for place in items:
            if place["id"] == place_id:
                return category
    return None


def apply_partner_flags_from_db():
    partners_map = get_partners_map()
    for place in all_places_list():
        if place["id"] in partners_map:
            place["is_partner"] = partners_map[place["id"]]


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


def track_place_view(place_id: str):
    inc_metric(f"view_place:{place_id}")
    category = get_place_category(place_id)
    if category:
        inc_metric(f"view_category:{category}")


def get_place_views(place_id: str) -> int:
    return get_metric(f"view_place:{place_id}")


def get_total_views() -> int:
    total = 0
    for place in all_places_list():
        total += get_place_views(place["id"])
    return total


def format_place(place: dict) -> str:
    partner_mark = "🔥 <b>Рекомендуем</b>\n" if place.get("is_partner", False) else ""
    order_mark = "🛒 Доступен заказ через бота\n" if place.get("is_partner", False) else ""
    return (
        f"{partner_mark}"
        f"{order_mark}"
        f"<b>{place['name']}</b>\n"
        f"📍 {place['address']}\n"
        f"⏰ {place['hours']}\n"
        f"⭐ {place['rating']}\n"
        f"💸 {place.get('budget', 'Нет данных')}\n"
        f"📝 {place['desc']}"
    )


def format_order_request(data: dict) -> str:
    return (
        "🛒 <b>Новая заявка</b>\n\n"
        f"🏠 Заведение: {data['place_name']}\n"
        f"👤 Имя: {data['customer_name']}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"📦 Формат: {data['mode']}\n"
        f"📍 Адрес: {data.get('address', 'Самовывоз')}\n"
        f"🍴 Заказ: {data['items']}\n"
        f"📝 Комментарий: {data['comment']}\n"
        f"🆔 User ID: {data['user_id']}"
    )


def popularity_score(place: dict) -> int:
    up, down = count_votes_db(place["id"])
    views = get_place_views(place["id"])
    partner_bonus = 3 if place.get("is_partner", False) else 0
    return (up * 3) - (down * 2) + views + partner_bonus


def sort_places_by_score(places: list[dict]) -> list[dict]:
    return sorted(
        places,
        key=lambda p: (
            p.get("is_partner", False),
            popularity_score(p),
            count_votes_db(p["id"])[0]
        ),
        reverse=True
    )


def get_partner_places() -> list[dict]:
    return [place for place in all_places_list() if place.get("is_partner", False)]


def get_total_votes() -> tuple[int, int]:
    total_likes = 0
    total_dislikes = 0
    for place in all_places_list():
        up, down = count_votes_db(place["id"])
        total_likes += up
        total_dislikes += down
    return total_likes, total_dislikes


def get_most_popular_places(limit: int = 5) -> list[dict]:
    return sort_places_by_score(all_places_list())[:limit]


def build_share_url() -> str:
    return f"https://t.me/{BOT_USERNAME}" if BOT_USERNAME else "https://t.me/"


def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍔 Бургеры"), KeyboardButton(text="🌯 Шаурма")],
            [KeyboardButton(text="🍕 Пицца"), KeyboardButton(text="☕ Кофе")],
            [KeyboardButton(text="🍺 Бары"), KeyboardButton(text="⭐ Лучшие места")],
            [KeyboardButton(text="🌙 Где поесть ночью"), KeyboardButton(text="🎲 Случайное место")],
            [KeyboardButton(text="🧠 Подобрать место"), KeyboardButton(text="🔥 Сейчас популярно")],
            [KeyboardButton(text="💑 Топ для свидания"), KeyboardButton(text="💸 Топ до 500")],
            [KeyboardButton(text="👥 Топ для компании"), KeyboardButton(text="🎯 Случайное по фильтру")],
            [KeyboardButton(text="🏆 Топ по категориям"), KeyboardButton(text="❤️ Моё избранное")],
            [KeyboardButton(text="ℹ️ Помощь")],
        ],
        resize_keyboard=True
    )


def get_top_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍔 Топ бургеры"), KeyboardButton(text="🌯 Топ шаурма")],
            [KeyboardButton(text="🍕 Топ пицца"), KeyboardButton(text="☕ Топ кофе")],
            [KeyboardButton(text="🍺 Топ бары")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True
    )


def get_back_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⬅️ Назад")]],
        resize_keyboard=True
    )


def get_budget_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💸 До 500"), KeyboardButton(text="💰 До 1000")],
            [KeyboardButton(text="💎 Не важно")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True
    )


def get_format_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Один"), KeyboardButton(text="💑 Свидание")],
            [KeyboardButton(text="👥 Компания")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True
    )


def get_food_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍔 Бургеры"), KeyboardButton(text="🌯 Шаурма")],
            [KeyboardButton(text="🍕 Пицца"), KeyboardButton(text="☕ Кофе")],
            [KeyboardButton(text="🍺 Бары"), KeyboardButton(text="🍽 Не важно")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True
    )


def get_distance_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚶 Рядом"), KeyboardButton(text="🚕 Не важно")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True
    )


def get_random_filter_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎲 Дешёвое случайное"), KeyboardButton(text="🎲 Для свидания")],
            [KeyboardButton(text="🎲 Ночное случайное"), KeyboardButton(text="🎲 Быстрый перекус")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True
    )


def get_order_mode_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚚 Доставка"), KeyboardButton(text="🏃 Самовывоз")],
            [KeyboardButton(text="❌ Отменить заказ")],
        ],
        resize_keyboard=True
    )


def get_cancel_order_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отменить заказ")]
        ],
        resize_keyboard=True
    )


def get_more_keyboard(cursor_key: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Ещё 5 мест", callback_data=f"more:{cursor_key}")]
        ]
    )


def card_buttons(place: dict) -> InlineKeyboardMarkup:
    up, down = count_votes_db(place["id"])
    share_url = (
        f"https://t.me/share/url?url={build_share_url()}"
        f"&text=Смотри, нашёл бота где можно выбрать место поесть в Каменске"
    )

    rows = [
        [InlineKeyboardButton(text="📍 Открыть в Яндекс Картах", url=place["url"])],
    ]

    if place.get("is_partner", False):
        rows.append(
            [InlineKeyboardButton(text="🛒 Оставить заказ", callback_data=f"order:{place['id']}")]
        )

    rows.extend([
        [InlineKeyboardButton(text="❤️ В избранное", callback_data=f"fav:{place['id']}")],
        [
            InlineKeyboardButton(text=f"👍 {up}", callback_data=f"like:{place['id']}"),
            InlineKeyboardButton(text=f"👎 {down}", callback_data=f"dislike:{place['id']}"),
        ],
        [InlineKeyboardButton(text="📤 Поделиться ботом", url=share_url)],
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


async def send_place_card(message: Message, place: dict):
    track_place_view(place["id"])
    await message.answer(
        format_place(place),
        parse_mode="HTML",
        reply_markup=card_buttons(place),
    )


async def send_ad_block(message: Message):
    await message.answer(random.choice(ADS), parse_mode="HTML")


async def send_places_with_ad(message: Message, places: list[dict], title: Optional[str] = None, limit: int = 5):
    if title:
        await message.answer(title, reply_markup=get_back_keyboard())

    if not places:
        await message.answer("Пока ничего не найдено.", reply_markup=get_back_keyboard())
        return

    key = f"user_{message.from_user.id}"
    USER_CONTEXT[key] = {"places": places, "offset": 0}

    for place in places[:limit]:
        await send_place_card(message, place)

    USER_CONTEXT[key]["offset"] = limit

    if len(places) > limit:
        await message.answer(
            "Показал первые места. Нажми, чтобы увидеть ещё:",
            reply_markup=get_more_keyboard(key)
        )

    await send_ad_block(message)


def smart_filter_places(
    budget: Optional[str] = None,
    fmt: Optional[str] = None,
    food: Optional[str] = None,
    distance: Optional[str] = None,
    night_only: bool = False,
) -> list[dict]:
    result = []
    for place in all_places_list():
        if budget and budget != "💎 Не важно" and place.get("budget") != budget:
            continue
        if fmt and fmt not in place.get("formats", []):
            continue
        if food and food != "🍽 Не важно" and place.get("food_type") != food:
            continue
        if distance == "🚶 Рядом" and place.get("distance") != "🚶 Рядом":
            continue
        if night_only and not place.get("night", False):
            continue
        result.append(place)
    return sort_places_by_score(result)


def format_admin_stats() -> str:
    metrics = get_metrics_map()
    users_count = len(get_all_users())
    places_count = len(all_places_list())
    partners_count = len(get_partner_places())
    likes, dislikes = get_total_votes()
    views = get_total_views()
    top_places = get_most_popular_places(5)
    orders_count = len(get_recent_orders(1000))

    lines = [
        "📊 <b>Статистика бота</b>",
        "",
        f"👥 Пользователей: {users_count}",
        f"📍 Всего заведений: {places_count}",
        f"🤝 Партнёров: {partners_count}",
        f"👀 Просмотров карточек: {views}",
        f"🛒 Заявок: {orders_count}",
        f"👍 Всего лайков: {likes}",
        f"👎 Всего дизлайков: {dislikes}",
        "",
        "📈 <b>Активность:</b>",
        f"▶️ /start: {metrics.get('start_used', 0)}",
        f"🧠 Подбор: {metrics.get('smart_used', 0)}",
        f"🎲 Случайное место: {metrics.get('random_used', 0)}",
        f"❤️ Избранное: {metrics.get('favorites_used', 0)}",
        f"🔥 Популярное: {metrics.get('popular_used', 0)}",
        f"🌙 Ночные подборки: {metrics.get('night_used', 0)}",
        f"💑 Топ для свидания: {metrics.get('top_date_used', 0)}",
        f"💸 Топ до 500: {metrics.get('top_budget_used', 0)}",
        f"👥 Топ для компании: {metrics.get('top_company_used', 0)}",
        f"🛒 Начатые заказы: {metrics.get('order_started', 0)}",
        f"✅ Отправленные заказы: {metrics.get('order_sent', 0)}",
        "",
        "📂 <b>Категории:</b>",
        f"🍔 Бургеры: {metrics.get('view_category:🍔 Бургеры', 0)}",
        f"🌯 Шаурма: {metrics.get('view_category:🌯 Шаурма', 0)}",
        f"🍕 Пицца: {metrics.get('view_category:🍕 Пицца', 0)}",
        f"☕ Кофе: {metrics.get('view_category:☕ Кофе', 0)}",
        f"🍺 Бары: {metrics.get('view_category:🍺 Бары', 0)}",
        "",
        "🔥 <b>Топ-5 популярных мест:</b>",
    ]

    if not top_places:
        lines.append("Пока нет данных.")
    else:
        for i, place in enumerate(top_places, start=1):
            up, down = count_votes_db(place["id"])
            lines.append(
                f"{i}. {place['name']} (👍 {up} / 👎 {down} / 👀 {get_place_views(place['id'])})"
            )

    return "\n".join(lines)


@dp.message(CommandStart())
async def start_handler(message: Message):
    save_user(message.from_user.id)
    inc_metric("start_used")
    await message.answer(
        "🍴 Где поесть в Каменске\n\nВыбери категорию или умный подбор:",
        reply_markup=get_main_keyboard()
    )


@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "👑 <b>Админ-панель</b>\n\n"
        "Команды:\n"
        "/admin — панель\n"
        "/stats — полная статистика\n"
        "/users — число пользователей\n"
        "/partners — список партнёров\n"
        "/promo — тест рекламного блока\n"
        "/orders — последние заявки\n"
        "/send текст — рассылка всем\n"
        "/partner_on place_id — включить партнёра\n"
        "/partner_off place_id — выключить партнёра",
        parse_mode="HTML"
    )


@dp.message(Command("stats"))
async def admin_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(format_admin_stats(), parse_mode="HTML")


@dp.message(Command("users"))
async def admin_users(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        f"👥 Пользователей в базе: <b>{len(get_all_users())}</b>",
        parse_mode="HTML"
    )


@dp.message(Command("partners"))
async def admin_partners(message: Message):
    if not is_admin(message.from_user.id):
        return

    partners = get_partner_places()
    if not partners:
        await message.answer("Партнёрских заведений пока нет.")
        return

    text = "🤝 <b>Партнёрские заведения:</b>\n\n"
    for place in partners:
        text += f"• {place['name']} — <code>{place['id']}</code>\n"

    await message.answer(text, parse_mode="HTML")


@dp.message(Command("promo"))
async def admin_promo(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(random.choice(ADS), parse_mode="HTML")


@dp.message(Command("orders"))
async def admin_orders(message: Message):
    if not is_admin(message.from_user.id):
        return

    orders = get_recent_orders(10)
    if not orders:
        await message.answer("Заявок пока нет.")
        return

    text = "🛒 <b>Последние заявки:</b>\n\n"
    for order_id, place_name, customer_name, phone, status, created_at in orders:
        text += (
            f"#{order_id} | {place_name}\n"
            f"👤 {customer_name}\n"
            f"📞 {phone}\n"
            f"📌 {status}\n"
            f"🕒 {created_at}\n\n"
        )

    await message.answer(text, parse_mode="HTML")


@dp.message(Command("send"))
async def send_broadcast(message: Message):
    if not is_admin(message.from_user.id):
        return

    text = message.text.replace("/send", "", 1).strip()
    if not text:
        await message.answer("Напиши текст после команды /send")
        return

    users = get_all_users()
    success = 0
    failed = 0

    for user_id in users:
        try:
            await bot.send_message(
                user_id,
                f"📢 <b>Обновление бота</b>\n\n{text}",
                parse_mode="HTML"
            )
            success += 1
        except Exception:
            failed += 1

    await message.answer(
        f"✅ Рассылка завершена\n\n"
        f"Успешно: {success}\n"
        f"Не доставлено: {failed}"
    )


@dp.message(Command("partner_on"))
async def partner_on_handler(message: Message):
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Используй: /partner_on place_id")
        return

    place_id = parts[1].strip()
    place = find_place_by_id(place_id)
    if not place:
        await message.answer("Заведение с таким place_id не найдено.")
        return

    place["is_partner"] = True
    set_partner_db(place_id, True)
    await message.answer(
        f"✅ Партнёр включён: <b>{place['name']}</b>",
        parse_mode="HTML"
    )


@dp.message(Command("partner_off"))
async def partner_off_handler(message: Message):
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Используй: /partner_off place_id")
        return

    place_id = parts[1].strip()
    place = find_place_by_id(place_id)
    if not place:
        await message.answer("Заведение с таким place_id не найдено.")
        return

    place["is_partner"] = False
    set_partner_db(place_id, False)
    await message.answer(
        f"❌ Партнёр выключен: <b>{place['name']}</b>",
        parse_mode="HTML"
    )


@dp.message(F.text == "ℹ️ Помощь")
@dp.message(F.text == "/help")
async def help_handler(message: Message):
    await message.answer(
        "Что умеет бот:\n\n"
        "• показывает заведения по категориям\n"
        "• умеет умно подбирать место\n"
        "• показывает лучшие и популярные места\n"
        "• помогает выбрать случайное место\n"
        "• показывает ночные варианты\n"
        "• умеет сохранять в избранное\n"
        "• считает лайки и дизлайки\n"
        "• позволяет делиться ботом\n"
        "• у партнёров можно оставить заявку на заказ\n\n"
        "Команды:\n"
        "/start — открыть меню\n"
        "/help — помощь",
        reply_markup=get_main_keyboard()
    )


@dp.message(F.text == "🏆 Топ по категориям")
async def top_menu_handler(message: Message):
    await message.answer("🏆 Выбери категорию:", reply_markup=get_top_keyboard())


@dp.message(F.text == "🍔 Топ бургеры")
async def top_burgers(message: Message):
    await send_places_with_ad(
        message,
        sort_places_by_score(PLACES["🍔 Бургеры"]),
        "🍔 Лучшие бургеры:"
    )


@dp.message(F.text == "🌯 Топ шаурма")
async def top_shaurma(message: Message):
    await send_places_with_ad(
        message,
        sort_places_by_score(PLACES["🌯 Шаурма"]),
        "🌯 Лучшая шаурма:"
    )


@dp.message(F.text == "🍕 Топ пицца")
async def top_pizza(message: Message):
    await send_places_with_ad(
        message,
        sort_places_by_score(PLACES["🍕 Пицца"]),
        "🍕 Лучшая пицца:"
    )


@dp.message(F.text == "☕ Топ кофе")
async def top_coffee(message: Message):
    await send_places_with_ad(
        message,
        sort_places_by_score(PLACES["☕ Кофе"]),
        "☕ Лучший кофе:"
    )


@dp.message(F.text == "🍺 Топ бары")
async def top_bars(message: Message):
    await send_places_with_ad(
        message,
        sort_places_by_score(PLACES["🍺 Бары"]),
        "🍺 Лучшие бары:"
    )


@dp.message(F.text == "🔥 Сейчас популярно")
async def popular_handler(message: Message):
    inc_metric("popular_used")
    await send_places_with_ad(
        message,
        get_most_popular_places(20),
        "🔥 Сейчас популярно в боте:",
        limit=5
    )


@dp.message(F.text == "💑 Топ для свидания")
async def top_for_date_handler(message: Message):
    inc_metric("top_date_used")
    await send_places_with_ad(
        message,
        smart_filter_places(fmt="💑 Свидание"),
        "💑 Лучшие места для свидания:",
        limit=5
    )


@dp.message(F.text == "💸 Топ до 500")
async def top_under_500_handler(message: Message):
    inc_metric("top_budget_used")
    await send_places_with_ad(
        message,
        smart_filter_places(budget="💸 До 500"),
        "💸 Лучшие места до 500:",
        limit=5
    )


@dp.message(F.text == "👥 Топ для компании")
async def top_for_company_handler(message: Message):
    inc_metric("top_company_used")
    await send_places_with_ad(
        message,
        smart_filter_places(fmt="👥 Компания"),
        "👥 Лучшие места для компании:",
        limit=5
    )


@dp.message(F.text == "🎯 Случайное по фильтру")
async def random_filter_menu_handler(message: Message):
    await message.answer(
        "🎯 Выбери сценарий:",
        reply_markup=get_random_filter_keyboard()
    )


@dp.message(F.text == "🎲 Дешёвое случайное")
async def random_budget_handler(message: Message):
    variants = smart_filter_places(budget="💸 До 500")
    if not variants:
        await message.answer("Ничего не найдено.", reply_markup=get_back_keyboard())
        return
    await message.answer("🎲 Дешёвый вариант:", reply_markup=get_back_keyboard())
    await send_place_card(message, random.choice(variants))


@dp.message(F.text == "🎲 Для свидания")
async def random_date_handler(message: Message):
    variants = smart_filter_places(fmt="💑 Свидание")
    if not variants:
        await message.answer("Ничего не найдено.", reply_markup=get_back_keyboard())
        return
    await message.answer("🎲 Вариант для свидания:", reply_markup=get_back_keyboard())
    await send_place_card(message, random.choice(variants))


@dp.message(F.text == "🎲 Ночное случайное")
async def random_night_handler(message: Message):
    variants = smart_filter_places(night_only=True)
    if not variants:
        await message.answer("Ничего не найдено.", reply_markup=get_back_keyboard())
        return
    await message.answer("🎲 Ночной вариант:", reply_markup=get_back_keyboard())
    await send_place_card(message, random.choice(variants))


@dp.message(F.text == "🎲 Быстрый перекус")
async def random_fast_handler(message: Message):
    fast = []
    for place in all_places_list():
        text = (place["name"] + " " + place["desc"]).lower()
        if any(word in text for word in ["шаурма", "бургер", "стритфуд", "фастфуд", "перекус"]):
            fast.append(place)

    fast = sort_places_by_score(fast)
    if not fast:
        await message.answer("Ничего не найдено.", reply_markup=get_back_keyboard())
        return

    await message.answer("🎲 Быстрый перекус:", reply_markup=get_back_keyboard())
    await send_place_card(message, random.choice(fast))


@dp.message(F.text == "🧠 Подобрать место")
async def smart_menu_handler(message: Message):
    inc_metric("smart_used")
    SMART_STATE[message.from_user.id] = {"step": "budget"}
    await message.answer(
        "🧠 Подберём место.\n\nСколько хочешь потратить?",
        reply_markup=get_budget_keyboard()
    )


@dp.message(F.text.in_(["💸 До 500", "💰 До 1000", "💎 Не важно"]))
async def smart_budget_handler(message: Message):
    state = SMART_STATE.get(message.from_user.id)
    if not state or state.get("step") != "budget":
        return

    state["budget"] = message.text
    state["step"] = "format"
    await message.answer("С кем идёшь?", reply_markup=get_format_keyboard())


@dp.message(F.text.in_(["👤 Один", "💑 Свидание", "👥 Компания"]))
async def smart_format_handler(message: Message):
    state = SMART_STATE.get(message.from_user.id)
    if not state or state.get("step") != "format":
        return

    state["format"] = message.text
    state["step"] = "food"
    await message.answer("Что хочется по еде?", reply_markup=get_food_keyboard())


@dp.message(F.text == "🍽 Не важно")
async def smart_food_any_handler(message: Message):
    state = SMART_STATE.get(message.from_user.id)
    if not state or state.get("step") != "food":
        return

    state["food"] = message.text
    state["step"] = "distance"
    await message.answer("Как по расстоянию?", reply_markup=get_distance_keyboard())


@dp.message(F.text.in_(PLACES.keys()))
async def category_or_smart_handler(message: Message):
    state = SMART_STATE.get(message.from_user.id)

    if state and state.get("step") == "food":
        state["food"] = message.text
        state["step"] = "distance"
        await message.answer("Как по расстоянию?", reply_markup=get_distance_keyboard())
        return

    category = message.text
    inc_metric(f"open_category:{category}")
    await send_places_with_ad(
        message,
        sort_places_by_score(PLACES[category]),
        f"{category} в Каменске-Уральском:",
        limit=5
    )


@dp.message(F.text.in_(["🚶 Рядом", "🚕 Не важно"]))
async def smart_distance_handler(message: Message):
    state = SMART_STATE.get(message.from_user.id)
    if not state or state.get("step") != "distance":
        return

    state["distance"] = message.text
    result = smart_filter_places(
        budget=state.get("budget"),
        fmt=state.get("format"),
        food=state.get("food"),
        distance=state.get("distance"),
    )
    SMART_STATE.pop(message.from_user.id, None)

    await send_places_with_ad(
        message,
        result,
        "🎯 Вот что лучше всего подходит тебе:",
        limit=5
    )


@dp.message(F.text == "⭐ Лучшие места")
async def top_handler(message: Message):
    await send_places_with_ad(
        message,
        sort_places_by_score(all_places_list())[:20],
        "⭐ Топ заведений по мнению пользователей:",
        limit=5
    )


@dp.message(F.text == "🌙 Где поесть ночью")
async def night_handler(message: Message):
    inc_metric("night_used")
    await send_places_with_ad(
        message,
        smart_filter_places(night_only=True),
        "🌙 Где поесть ночью:",
        limit=5
    )


@dp.message(F.text == "🎲 Случайное место")
async def random_handler(message: Message):
    inc_metric("random_used")
    place = random.choice(all_places_list())
    await message.answer("🎲 Сегодня попробуй:", reply_markup=get_back_keyboard())
    await send_place_card(message, place)


@dp.message(F.text == "❤️ Моё избранное")
async def favorites_handler(message: Message):
    save_user(message.from_user.id)
    inc_metric("favorites_used")

    favorite_ids = get_favorites_db(message.from_user.id)
    if not favorite_ids:
        await message.answer("У тебя пока нет избранных мест.", reply_markup=get_back_keyboard())
        return

    places = []
    for place_id in favorite_ids:
        place = find_place_by_id(place_id)
        if place:
            places.append(place)

    await send_places_with_ad(
        message,
        sort_places_by_score(places),
        "❤️ Твоё избранное:",
        limit=5
    )


@dp.message(F.text == "💸 Дёшево")
async def cheap_handler(message: Message):
    await send_places_with_ad(
        message,
        smart_filter_places(budget="💸 До 500"),
        "💸 Недорогие варианты:",
        limit=5
    )


@dp.message(F.text == "⚡ Быстро")
async def fast_handler(message: Message):
    result = []
    for place in all_places_list():
        text = (place["name"] + " " + place["desc"]).lower()
        if any(word in text for word in ["шаурма", "бургер", "стритфуд", "фастфуд", "перекус"]):
            result.append(place)

    await send_places_with_ad(
        message,
        sort_places_by_score(result),
        "⚡ Быстрый перекус:",
        limit=5
    )


@dp.message(F.text == "☕ Посидеть")
async def chill_handler(message: Message):
    result = [p for p in all_places_list() if p.get("food_type") in ["☕ Кофе", "🍺 Бары"]]
    await send_places_with_ad(
        message,
        sort_places_by_score(result),
        "☕ Где можно посидеть:",
        limit=5
    )


@dp.callback_query(F.data.startswith("order:"))
async def start_order_handler(callback: CallbackQuery):
    place_id = callback.data.split(":", 1)[1]
    place = find_place_by_id(place_id)

    if not place:
        await callback.answer("Заведение не найдено", show_alert=True)
        return

    if not place.get("is_partner", False):
        await callback.answer("Заказ доступен только у партнёров", show_alert=True)
        return

    ORDER_STATE[callback.from_user.id] = {
        "step": "items",
        "place_id": place["id"],
        "place_name": place["name"],
        "user_id": callback.from_user.id,
    }

    inc_metric("order_started")

    await callback.message.answer(
        f"🛒 Заказ в <b>{place['name']}</b>\n\n"
        "Напиши, что хочешь заказать.\n"
        "Например: 2 шаурмы, картошка, кола",
        parse_mode="HTML",
        reply_markup=get_cancel_order_keyboard()
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("fav:"))
async def add_to_favorites_handler(callback: CallbackQuery):
    save_user(callback.from_user.id)
    place_id = callback.data.split(":", 1)[1]
    place = find_place_by_id(place_id)

    if not place:
        await callback.answer("Место не найдено", show_alert=True)
        return

    favorite_ids = get_favorites_db(callback.from_user.id)
    if place_id in favorite_ids:
        await callback.answer("Уже в избранном ❤️")
        return

    add_favorite_db(callback.from_user.id, place_id)
    await callback.answer("Добавлено в избранное ❤️")


@dp.callback_query(F.data.startswith("like:"))
async def like_handler(callback: CallbackQuery):
    save_user(callback.from_user.id)
    place_id = callback.data.split(":", 1)[1]
    place = find_place_by_id(place_id)

    if not place:
        await callback.answer("Место не найдено", show_alert=True)
        return

    if get_vote_db(callback.from_user.id, place_id) == "like":
        await callback.answer("Ты уже поставил 👍")
        return

    set_vote_db(callback.from_user.id, place_id, "like")
    await callback.message.edit_reply_markup(reply_markup=card_buttons(place))
    await callback.answer("Ты поставил 👍")


@dp.callback_query(F.data.startswith("dislike:"))
async def dislike_handler(callback: CallbackQuery):
    save_user(callback.from_user.id)
    place_id = callback.data.split(":", 1)[1]
    place = find_place_by_id(place_id)

    if not place:
        await callback.answer("Место не найдено", show_alert=True)
        return

    if get_vote_db(callback.from_user.id, place_id) == "dislike":
        await callback.answer("Ты уже поставил 👎")
        return

    set_vote_db(callback.from_user.id, place_id, "dislike")
    await callback.message.edit_reply_markup(reply_markup=card_buttons(place))
    await callback.answer("Ты поставил 👎")


@dp.callback_query(F.data.startswith("more:"))
async def more_places_handler(callback: CallbackQuery):
    key = callback.data.split(":", 1)[1]
    context = USER_CONTEXT.get(key)

    if not context:
        await callback.answer("Больше мест нет")
        return

    places = context["places"]
    offset = context["offset"]
    next_chunk = places[offset: offset + 5]

    if not next_chunk:
        await callback.answer("Это были все места")
        return

    for place in next_chunk:
        await send_place_card(callback.message, place)

    context["offset"] = offset + 5

    if context["offset"] < len(places):
        await callback.message.answer("Показать ещё?", reply_markup=get_more_keyboard(key))
    else:
        await callback.message.answer("✅ Это все найденные места.")

    await callback.answer()


@dp.message(F.text == "❌ Отменить заказ")
async def cancel_order_handler(message: Message):
    if message.from_user.id in ORDER_STATE:
        ORDER_STATE.pop(message.from_user.id, None)
        await message.answer("❌ Заказ отменён.", reply_markup=get_main_keyboard())


@dp.message(F.text == "⬅️ Назад")
async def back_handler(message: Message):
    SMART_STATE.pop(message.from_user.id, None)
    ORDER_STATE.pop(message.from_user.id, None)
    await message.answer(
        "🍴 Снова главное меню\n\nВыбери категорию:",
        reply_markup=get_main_keyboard()
    )


@dp.message()
async def order_flow_handler(message: Message):
    state = ORDER_STATE.get(message.from_user.id)
    if not state:
        await fallback_handler(message)
        return

    step = state.get("step")

    if step == "items":
        state["items"] = message.text.strip()
        state["step"] = "name"
        await message.answer(
            "👤 Напиши своё имя:",
            reply_markup=get_cancel_order_keyboard()
        )
        return

    if step == "name":
        state["customer_name"] = message.text.strip()
        state["step"] = "phone"
        await message.answer(
            "📞 Напиши телефон для связи:",
            reply_markup=get_cancel_order_keyboard()
        )
        return

    if step == "phone":
        state["phone"] = message.text.strip()
        state["step"] = "mode"
        await message.answer(
            "📦 Выбери способ получения:",
            reply_markup=get_order_mode_keyboard()
        )
        return

    if step == "mode":
        if message.text not in ["🚚 Доставка", "🏃 Самовывоз"]:
            await message.answer("Выбери один из вариантов: доставка или самовывоз.")
            return

        state["mode"] = message.text

        if message.text == "🚚 Доставка":
            state["step"] = "address"
            await message.answer(
                "📍 Напиши адрес доставки:",
                reply_markup=get_cancel_order_keyboard()
            )
        else:
            state["address"] = "Самовывоз"
            state["step"] = "comment"
            await message.answer(
                "📝 Напиши комментарий к заказу или отправь '-' если без комментария:",
                reply_markup=get_cancel_order_keyboard()
            )
        return

    if step == "address":
        state["address"] = message.text.strip()
        state["step"] = "comment"
        await message.answer(
            "📝 Напиши комментарий к заказу или отправь '-' если без комментария:",
            reply_markup=get_cancel_order_keyboard()
        )
        return

    if step == "comment":
        state["comment"] = message.text.strip()

        try:
            save_order_db(state)
            await bot.send_message(
                ADMIN_ID,
                format_order_request(state),
                parse_mode="HTML"
            )
        except Exception:
            await message.answer(
                "⚠️ Не удалось отправить заявку. Попробуй позже.",
                reply_markup=get_main_keyboard()
            )
            ORDER_STATE.pop(message.from_user.id, None)
            return

        inc_metric("order_sent")

        await message.answer(
            "✅ Заявка отправлена.\n\nС тобой скоро свяжутся для подтверждения заказа.",
            reply_markup=get_main_keyboard()
        )

        ORDER_STATE.pop(message.from_user.id, None)
        return


async def fallback_handler(message: Message):
    save_user(message.from_user.id)
    await message.answer(
        "Нажми /start и выбери кнопку из меню.",
        reply_markup=get_main_keyboard()
    )


async def main():
    global BOT_USERNAME

    init_db()
    apply_partner_flags_from_db()

    me = await bot.get_me()
    BOT_USERNAME = me.username

    print(f"BOT STARTED: @{me.username}", flush=True)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
