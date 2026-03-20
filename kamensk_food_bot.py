import os
import asyncio
import random
import sqlite3

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
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

ADMIN_ID = int(os.getenv("ADMIN_ID", 729024995))
DB_PATH = "bot.db"

bot = Bot(token=TOKEN)
dp = Dispatcher()

USERS = set()


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

    conn.commit()
    conn.close()


def save_user(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()


def get_all_users():
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


def get_favorites_db(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT place_id FROM favorites WHERE user_id = ?",
        (user_id,)
    )
    rows = cur.fetchall()
    conn.close()
    return [row[0] for row in rows]


def get_vote_db(user_id: int, place_id: str):
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
        ON CONFLICT(user_id, place_id) DO UPDATE SET vote=excluded.vote
    """, (user_id, place_id, vote))
    conn.commit()
    conn.close()


def count_votes_db(place_id: str):
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
            "photo": "https://1000logos.net/wp-content/uploads/2017/03/Burger-King-Logo.png",
            "photo_page": "https://yandex.ru/maps/?text=Каменск-Уральский Бургер Кинг проспект Победы 65",
            "is_partner": False,
        },
        {
            "id": "burger_2",
            "name": "Rostic's",
            "address": "ул. Суворова, 24",
            "hours": "До 00:00",
            "rating": "4.2",
            "desc": "Курица, бургеры, баскеты и комбо.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Rostic's Суворова 24",
            "photo": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5b/Rostics_logo.svg/512px-Rostics_logo.svg.png",
            "photo_page": "https://yandex.ru/maps/?text=Каменск-Уральский Rostic's Суворова 24",
            "is_partner": False,
        },
        {
            "id": "burger_3",
            "name": "Шампурико",
            "address": "Алюминиевая ул., 77Б",
            "hours": "С 10:30",
            "rating": "4.9",
            "desc": "Стритфуд, мясо и блюда на гриле.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Шампурико Алюминиевая 77Б",
            "photo": None,
            "photo_page": "https://2gis.ru/k_uralskiy/gallery/firm/70000001097374790",
            "is_partner": False,
        },
        {
            "id": "burger_4",
            "name": "Седьмое небо",
            "address": "Каменская ул., 79Б",
            "hours": "Уточняй в картах",
            "rating": "4.7",
            "desc": "Стритфуд, бургеры, шаурма и пицца.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Седьмое небо Каменская 79Б",
            "photo": None,
            "photo_page": "https://nebo-7.ru/",
            "is_partner": False,
        },
        {
            "id": "burger_5",
            "name": "Subjoy",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.2",
            "desc": "Сэндвичи, бургеры и быстрый перекус.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Subjoy",
            "photo": None,
            "photo_page": "https://yandex.ru/maps/?text=Каменск-Уральский Subjoy",
            "is_partner": False,
        },
        {
            "id": "burger_6",
            "name": "Русская забава",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.4",
            "desc": "Фастфуд и закуски.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Русская забава",
            "photo": None,
            "photo_page": "https://yandex.ru/maps/?text=Каменск-Уральский Русская забава",
            "is_partner": False,
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
            "photo": None,
            "photo_page": "https://yandex.ru/maps/org/shaurma_market/75638569554/gallery/",
            "is_partner": False,
        },
        {
            "id": "shawarma_2",
            "name": "Лаваш",
            "address": "Алюминиевая ул., 78",
            "hours": "С 09:00",
            "rating": "4.5",
            "desc": "Шаверма, хот-доги и быстрые закуски.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Лаваш Алюминиевая 78",
            "photo": None,
            "photo_page": "https://yandex.ru/maps/?text=Каменск-Уральский Лаваш Алюминиевая 78",
            "is_partner": False,
        },
        {
            "id": "shawarma_3",
            "name": "Мясной Батя",
            "address": "просп. Победы, 75Б",
            "hours": "С 10:00",
            "rating": "4.3",
            "desc": "Шаурма и мясо на гриле.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Мясной Батя проспект Победы 75Б",
            "photo": None,
            "photo_page": "https://yandex.ru/maps/?text=Каменск-Уральский Мясной Батя проспект Победы 75Б",
            "is_partner": False,
        },
        {
            "id": "shawarma_4",
            "name": "По шаурме",
            "address": "просп. Победы, 19",
            "hours": "Уточняй в картах",
            "rating": "Нет данных",
            "desc": "Шаурма и быстрый перекус.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский По шаурме проспект Победы 19",
            "photo": None,
            "photo_page": "https://yandex.ru/maps/?text=Каменск-Уральский По шаурме проспект Победы 19",
            "is_partner": False,
        },
        {
            "id": "shawarma_5",
            "name": "Шаурма",
            "address": "Каменская ул., 82Б",
            "hours": "С 09:00",
            "rating": "4.6",
            "desc": "Точка с классической шаурмой.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Шаурма Каменская 82Б",
            "photo": None,
            "photo_page": "https://2gis.ru/k_uralskiy/firm/70000001039954042",
            "is_partner": False,
        },
        {
            "id": "shawarma_6",
            "name": "Шаурма восточная",
            "address": "ул. Бугарева, 3",
            "hours": "Уточняй в картах",
            "rating": "Нет данных",
            "desc": "Восточная шаурма и закуски.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Шаурма восточная Бугарева 3",
            "photo": None,
            "photo_page": "https://yandex.ru/maps/?text=Каменск-Уральский Шаурма восточная Бугарева 3",
            "is_partner": False,
        },
        {
            "id": "shawarma_7",
            "name": "Мангал",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.7",
            "desc": "Шаурма, мясо и блюда на мангале.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Мангал",
            "photo": None,
            "photo_page": "https://yandex.ru/maps/?text=Каменск-Уральский Мангал",
            "is_partner": False,
        },
        {
            "id": "shawarma_8",
            "name": "Седьмое небо",
            "address": "Каменская ул., 79Б",
            "hours": "Уточняй в картах",
            "rating": "4.7",
            "desc": "Шаурма, бургеры и пицца.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Седьмое небо Каменская 79Б",
            "photo": None,
            "photo_page": "https://nebo-7.ru/",
            "is_partner": False,
        },
        {
            "id": "shawarma_9",
            "name": "Шампурико",
            "address": "Алюминиевая ул., 77Б",
            "hours": "С 10:30",
            "rating": "4.9",
            "desc": "Шаурма и блюда на гриле.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Шампурико Алюминиевая 77Б",
            "photo": None,
            "photo_page": "https://2gis.ru/k_uralskiy/gallery/firm/70000001097374790",
            "is_partner": False,
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
            "photo": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/Dodo_Pizza_logo.svg/512px-Dodo_Pizza_logo.svg.png",
            "photo_page": "https://yandex.ru/maps/?text=Каменск-Уральский Додо Пицца Каменская 91",
            "is_partner": False,
        },
        {
            "id": "pizza_2",
            "name": "Додо Пицца",
            "address": "просп. Победы, 44",
            "hours": "Уточняй в картах",
            "rating": "4.8",
            "desc": "Ещё одна точка Додо Пиццы.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Додо Пицца проспект Победы 44",
            "photo": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/Dodo_Pizza_logo.svg/512px-Dodo_Pizza_logo.svg.png",
            "photo_page": "https://yandex.ru/maps/?text=Каменск-Уральский Додо Пицца проспект Победы 44",
            "is_partner": False,
        },
        {
            "id": "pizza_3",
            "name": "Pizza Mia",
            "address": "ул. Суворова, 18",
            "hours": "С 11:00",
            "rating": "4.5",
            "desc": "Пицца и быстрые обеды.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Pizza Mia Суворова 18",
            "photo": None,
            "photo_page": "https://yandex.ru/maps/?text=Каменск-Уральский Pizza Mia Суворова 18",
            "is_partner": False,
        },
        {
            "id": "pizza_4",
            "name": "Pizza Mia",
            "address": "просп. Победы, 51А",
            "hours": "С 11:00",
            "rating": "4.2",
            "desc": "Пицца, закуски и семейный формат.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Pizza Mia проспект Победы 51А",
            "photo": None,
            "photo_page": "https://yandex.ru/maps/?text=Каменск-Уральский Pizza Mia проспект Победы 51А",
            "is_partner": False,
        },
        {
            "id": "pizza_5",
            "name": "Италиан Пицца",
            "address": "ул. Суворова, 23А",
            "hours": "С 09:00",
            "rating": "4.9",
            "desc": "Пицца и итальянское меню.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Италиан Пицца Суворова 23А",
            "photo": None,
            "photo_page": "https://yandex.ru/maps/?text=Каменск-Уральский Италиан Пицца Суворова 23А",
            "is_partner": False,
        },
        {
            "id": "pizza_6",
            "name": "Италиан Пицца",
            "address": "просп. Победы, 44",
            "hours": "Уточняй в картах",
            "rating": "4.9",
            "desc": "Ещё одна точка Италиан Пиццы.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Италиан Пицца проспект Победы 44",
            "photo": None,
            "photo_page": "https://yandex.ru/maps/?text=Каменск-Уральский Италиан Пицца проспект Победы 44",
            "is_partner": False,
        },
        {
            "id": "pizza_7",
            "name": "Pizzatime",
            "address": "Каменская ул., 12",
            "hours": "С 12:00",
            "rating": "Нет данных",
            "desc": "Пицца и быстрый перекус.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Pizzatime Каменская 12",
            "photo": None,
            "photo_page": "https://yandex.ru/maps/?text=Каменск-Уральский Pizzatime Каменская 12",
            "is_partner": False,
        },
        {
            "id": "pizza_8",
            "name": "Sushkof i Pizza",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.5",
            "desc": "Пицца, роллы и доставка.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Sushkof i Pizza",
            "photo": None,
            "photo_page": "https://yandex.ru/maps/?text=Каменск-Уральский Sushkof i Pizza",
            "is_partner": False,
        },
        {
            "id": "pizza_9",
            "name": "Большие тарелки",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.3",
            "desc": "Пицца, горячие блюда и кафе-формат.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Большие тарелки",
            "photo": None,
            "photo_page": "https://2gis.ru/k_uralskiy/search/%D0%91%D0%BE%D0%BB%D1%8C%D1%88%D0%B8%D0%B5%20%D1%82%D0%B0%D1%80%D0%B5%D0%BB%D0%BA%D0%B8",
            "is_partner": False,
        },
        {
            "id": "pizza_10",
            "name": "Седьмое небо",
            "address": "Каменская ул., 79Б",
            "hours": "Уточняй в картах",
            "rating": "4.7",
            "desc": "Стритфуд, шаурма и пицца.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Седьмое небо Каменская 79Б",
            "photo": None,
            "photo_page": "https://nebo-7.ru/",
            "is_partner": False,
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
            "photo": None,
            "photo_page": "https://2gis.ru/k_uralskiy/firm/70000001088171495",
            "is_partner": False,
        },
        {
            "id": "coffee_2",
            "name": "Черный лис",
            "address": "просп. Победы, 6",
            "hours": "Уточняй в картах",
            "rating": "4.5",
            "desc": "Кофе с собой и десерты.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Черный лис проспект Победы 6",
            "photo": None,
            "photo_page": "https://2gis.ru/k_uralskiy/firm/70000001036235498",
            "is_partner": False,
        },
        {
            "id": "coffee_3",
            "name": "Черный лис",
            "address": "Алюминиевая ул., 68",
            "hours": "Уточняй в картах",
            "rating": "4.5",
            "desc": "Ещё одна точка кофейни Черный лис.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Черный лис Алюминиевая 68",
            "photo": None,
            "photo_page": "https://2gis.ru/k_uralskiy/firm/70000001090689760",
            "is_partner": False,
        },
        {
            "id": "coffee_4",
            "name": "Coffee Print",
            "address": "просп. Победы, 65",
            "hours": "С 10:00",
            "rating": "5.0",
            "desc": "Кофе, выпечка и перекус.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Coffee Print проспект Победы 65",
            "photo": None,
            "photo_page": "https://2gis.ru/k_uralskiy/firm/70000001055315793",
            "is_partner": False,
        },
        {
            "id": "coffee_5",
            "name": "По любви",
            "address": "Алюминиевая ул., 37",
            "hours": "Уточняй в картах",
            "rating": "4.4",
            "desc": "Кофейня и десерты.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский По любви Алюминиевая 37",
            "photo": None,
            "photo_page": "https://2gis.ru/k_uralskiy/firm/70000001065981951",
            "is_partner": False,
        },
        {
            "id": "coffee_6",
            "name": "Это твой кофе",
            "address": "ул. Суворова, 24",
            "hours": "Уточняй в картах",
            "rating": "Нет данных",
            "desc": "Кофе с собой.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Это твой кофе Суворова 24",
            "photo": None,
            "photo_page": "https://yandex.ru/maps/?text=Каменск-Уральский Это твой кофе Суворова 24",
            "is_partner": False,
        },
        {
            "id": "coffee_7",
            "name": "Bubble Cafe",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.5",
            "desc": "Напитки, десерты и кафе-формат.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Bubble Cafe",
            "photo": None,
            "photo_page": "https://2gis.ru/k_uralskiy/firm/70000001096874801",
            "is_partner": False,
        },
        {
            "id": "coffee_8",
            "name": "Avokado Gold",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.4",
            "desc": "Кафе и кофейные напитки.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Avokado Gold",
            "photo": None,
            "photo_page": "https://2gis.ru/k_uralskiy/search/Avokado%20Gold",
            "is_partner": False,
        },
        {
            "id": "coffee_9",
            "name": "На Берегу",
            "address": "Набережная ул., 9",
            "hours": "Уточняй в картах",
            "rating": "4.4",
            "desc": "Кофе и спокойное место.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский На Берегу Набережная 9",
            "photo": None,
            "photo_page": "https://yandex.ru/maps/?text=Каменск-Уральский На Берегу Набережная 9",
            "is_partner": False,
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
            "photo": None,
            "photo_page": "https://2gis.ru/k_uralskiy/gallery/firm/70000001036731602",
            "is_partner": False,
        },
        {
            "id": "bar_2",
            "name": "Моджо",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.5",
            "desc": "Бар с вечерней атмосферой.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Моджо",
            "photo": None,
            "photo_page": "https://2gis.ru/k_uralskiy/firm/70000001006952161",
            "is_partner": False,
        },
        {
            "id": "bar_3",
            "name": "K1",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.6",
            "desc": "Бар и место для вечернего отдыха.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский K1",
            "photo": None,
            "photo_page": "https://yandex.ru/maps/?text=Каменск-Уральский K1",
            "is_partner": False,
        },
        {
            "id": "bar_4",
            "name": "Генрих и Генриетта",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.4",
            "desc": "Бар / паб-формат.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Генрих и Генриетта",
            "photo": None,
            "photo_page": "https://2gis.ru/k_uralskiy/gallery/firm/70000001006952917",
            "is_partner": False,
        },
        {
            "id": "bar_5",
            "name": "Шахта",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.3",
            "desc": "Бар и вечерний отдых.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Шахта",
            "photo": None,
            "photo_page": "https://yandex.ru/maps/?text=Каменск-Уральский Шахта",
            "is_partner": False,
        },
        {
            "id": "bar_6",
            "name": "Роял Рум",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "4.0",
            "desc": "Бар и клубный формат.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Роял Рум",
            "photo": None,
            "photo_page": "https://yandex.ru/maps/?text=Каменск-Уральский Роял Рум",
            "is_partner": False,
        },
        {
            "id": "bar_7",
            "name": "Седьмое небо",
            "address": "Адрес уточняй в картах",
            "hours": "Уточняй в картах",
            "rating": "Нет данных",
            "desc": "Бар / кафе-формат.",
            "url": "https://yandex.ru/maps/?text=Каменск-Уральский Седьмое небо бар",
            "photo": None,
            "photo_page": "https://nebo-7.ru/",
            "is_partner": False,
        },
    ],
}

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
            [KeyboardButton(text="🧠 Подобрать место")],
            [KeyboardButton(text="🏆 Топ по категориям")],
            [KeyboardButton(text="❤️ Моё избранное")],
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
    return count_votes_db(place_id)


def get_place_rating_score(place: dict) -> int:
    up, down = count_votes_db(place["id"])
    return up - down


def sort_places_by_score(places: list[dict]) -> list[dict]:
    return sorted(
        places,
        key=lambda p: (
            p.get("is_partner", False),
            get_place_rating_score(p),
            count_votes_db(p["id"])[0]
        ),
        reverse=True
    )


def card_buttons(place: dict) -> InlineKeyboardMarkup:
    up, down = get_place_score(place["id"])

    buttons = [
        [InlineKeyboardButton(text="📍 Открыть в Яндекс Картах", url=place["url"])]
    ]

    if place.get("photo_page"):
        buttons.append(
            [InlineKeyboardButton(text="🖼 Фото заведения", url=place["photo_page"])]
        )

    buttons.append(
        [InlineKeyboardButton(text="❤️ В избранное", callback_data=f"fav:{place['id']}")]
    )

    buttons.append(
        [
            InlineKeyboardButton(text=f"👍 {up}", callback_data=f"like:{place['id']}"),
            InlineKeyboardButton(text=f"👎 {down}", callback_data=f"dislike:{place['id']}"),
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


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
    partner_mark = "🤝 Партнёр\n" if place.get("is_partner", False) else ""
    return (
        f"{partner_mark}"
        f"<b>{place['name']}</b>\n"
        f"📍 {place['address']}\n"
        f"⏰ {place['hours']}\n"
        f"⭐ {place['rating']}\n"
        f"📝 {place['desc']}"
    )


async def send_place_card(message: Message, place: dict):
    text = format_place(place)

    if place.get("photo"):
        try:
            await message.answer_photo(
                photo=place["photo"],
                caption=text,
                parse_mode="HTML",
                reply_markup=card_buttons(place),
            )
            return
        except Exception:
            pass

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=card_buttons(place),
    )


@dp.message(CommandStart())
async def start_handler(message: Message):
    USERS.add(message.from_user.id)
    save_user(message.from_user.id)
    await message.answer(
        "🍴 Где поесть в Каменске\n\nВыбери категорию:",
        reply_markup=get_main_keyboard()
    )


@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    users = get_all_users()

    await message.answer(
        f"👑 Админ-панель\n\n"
        f"👥 Пользователей в базе: {len(users)}\n\n"
        f"Для рассылки:\n"
        f"/send Твой текст рекламы"
    )


@dp.message(Command("send"))
async def send_broadcast(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    text = message.text.replace("/send", "", 1).strip()
    if not text:
        await message.answer("Напиши текст после команды /send")
        return

    users = get_all_users()
    success = 0

    for user_id in users:
        try:
            await bot.send_message(
                user_id,
                f"📢 <b>Реклама</b>\n\n{text}",
                parse_mode="HTML"
            )
            success += 1
        except Exception:
            pass

    await message.answer(f"✅ Отправлено: {success}")


@dp.message(F.text == "ℹ️ Помощь")
@dp.message(F.text == "/help")
async def help_handler(message: Message):
    await message.answer(
        "Что умеет бот:\n\n"
        "• показывает заведения по категориям\n"
        "• открывает заведения в Яндекс Картах\n"
        "• открывает страницы с фото заведений\n"
        "• показывает лучшие места\n"
        "• показывает места, где можно поесть ночью\n"
        "• выбирает случайное место\n"
        "• умеет сохранять места в избранное\n"
        "• умеет считать лайки и дизлайки\n"
        "• умеет подбирать места по сценарию\n\n"
        "Команды:\n"
        "/start — открыть меню\n"
        "/help — помощь"
    )


@dp.message(F.text == "🏆 Топ по категориям")
async def top_menu_handler(message: Message):
    await message.answer(
        "🏆 Выбери категорию:",
        reply_markup=get_top_keyboard()
    )


async def send_top(message: Message, category: str, title: str):
    places = PLACES.get(category, [])
    places = sort_places_by_score(places)[:5]

    await message.answer(title, reply_markup=get_back_keyboard())

    if not places:
        await message.answer("Пока нет данных.")
        return

    for place in places:
        await send_place_card(message, place)


@dp.message(F.text == "🍔 Топ бургеры")
async def top_burgers(message: Message):
    await send_top(message, "🍔 Бургеры", "🍔 Лучшие бургеры:")


@dp.message(F.text == "🌯 Топ шаурма")
async def top_shaurma(message: Message):
    await send_top(message, "🌯 Шаурма", "🌯 Лучшая шаурма:")


@dp.message(F.text == "🍕 Топ пицца")
async def top_pizza(message: Message):
    await send_top(message, "🍕 Пицца", "🍕 Лучшая пицца:")


@dp.message(F.text == "☕ Топ кофе")
async def top_coffee(message: Message):
    await send_top(message, "☕ Кофе", "☕ Лучший кофе:")


@dp.message(F.text == "🍺 Топ бары")
async def top_bars(message: Message):
    await send_top(message, "🍺 Бары", "🍺 Лучшие бары:")


@dp.message(F.text == "🧠 Подобрать место")
async def smart_menu_handler(message: Message):
    await message.answer(
        "Выбери, что ты хочешь:",
        reply_markup=get_smart_keyboard()
    )


@dp.message(F.text == "💸 Дёшево")
async def cheap_handler(message: Message):
    cheap_keywords = ["шаурма", "шаверма", "бургер", "стритфуд", "перекус", "фастфуд"]

    result = []
    for place in all_places_list():
        text = (place["name"] + " " + place["desc"]).lower()
        if any(word in text for word in cheap_keywords):
            result.append(place)

    result = sort_places_by_score(result)[:5]

    await message.answer("💸 Недорогие варианты:", reply_markup=get_back_keyboard())

    if not result:
        await message.answer("Пока ничего не найдено.")
        return

    for place in result:
        await send_place_card(message, place)


@dp.message(F.text == "⚡ Быстро")
async def fast_handler(message: Message):
    fast_categories = ["🍔 Бургеры", "🌯 Шаурма"]
    result = []

    for cat in fast_categories:
        result.extend(PLACES.get(cat, []))

    result = sort_places_by_score(result)[:5]

    await message.answer("⚡ Быстрый перекус:", reply_markup=get_back_keyboard())

    if not result:
        await message.answer("Пока ничего не найдено.")
        return

    for place in result:
        await send_place_card(message, place)


@dp.message(F.text == "☕ Посидеть")
async def chill_handler(message: Message):
    result = PLACES.get("☕ Кофе", []) + PLACES.get("🍺 Бары", [])
    result = sort_places_by_score(result)[:6]

    await message.answer("☕ Где можно посидеть:", reply_markup=get_back_keyboard())

    if not result:
        await message.answer("Пока ничего не найдено.")
        return

    for place in result:
        await send_place_card(message, place)


@dp.message(F.text == "🌙 Ночью")
async def night_smart_handler(message: Message):
    result = []

    for name in NIGHT_PLACES:
        place = find_place_by_name(name)
        if place:
            result.append(place)

    result = sort_places_by_score(result)

    await message.answer("🌙 Где поесть ночью:", reply_markup=get_back_keyboard())

    if not result:
        await message.answer("Пока ничего не найдено.")
        return

    for place in result:
        await send_place_card(message, place)


@dp.message(F.text.in_(PLACES.keys()))
async def category_handler(message: Message):
    category = message.text
    sorted_places = sort_places_by_score(PLACES[category])

    await message.answer(
        f"{category} в Каменске-Уральском:",
        reply_markup=get_back_keyboard()
    )

    for place in sorted_places:
        await send_place_card(message, place)


@dp.message(F.text == "⭐ Лучшие места")
async def top_handler(message: Message):
    all_places = sort_places_by_score(all_places_list())
    top_places = all_places[:10]

    await message.answer(
        "⭐ Топ заведений по мнению пользователей:",
        reply_markup=get_back_keyboard()
    )

    if not top_places:
        await message.answer("Пока нет оценок.")
        return

    for place in top_places:
        await send_place_card(message, place)


@dp.message(F.text == "🌙 Где поесть ночью")
async def night_handler(message: Message):
    await message.answer(
        "🌙 Места, которые часто работают допоздна:",
        reply_markup=get_back_keyboard()
    )

    for name in NIGHT_PLACES:
        place = find_place_by_name(name)
        if place:
            await send_place_card(message, place)


@dp.message(F.text == "🎲 Случайное место")
async def random_handler(message: Message):
    place = random.choice(all_places_list())
    await message.answer(
        "🎲 Сегодня попробуй:",
        reply_markup=get_back_keyboard()
    )
    await send_place_card(message, place)


@dp.message(F.text == "❤️ Моё избранное")
async def favorites_handler(message: Message):
    user_id = message.from_user.id
    save_user(user_id)

    favorite_ids = get_favorites_db(user_id)

    if not favorite_ids:
        await message.answer(
            "У тебя пока нет избранных мест.",
            reply_markup=get_back_keyboard()
        )
        return

    await message.answer(
        "❤️ Твоё избранное:",
        reply_markup=get_back_keyboard()
    )

    for place_id in favorite_ids:
        place = find_place_by_id(place_id)
        if place:
            await send_place_card(message, place)


@dp.callback_query(F.data.startswith("fav:"))
async def add_to_favorites_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    save_user(user_id)

    place_id = callback.data.split(":", 1)[1]
    place = find_place_by_id(place_id)

    if not place:
        await callback.answer("Место не найдено", show_alert=True)
        return

    favorite_ids = get_favorites_db(user_id)

    if place_id in favorite_ids:
        await callback.answer("Уже в избранном ❤️", show_alert=False)
        return

    add_favorite_db(user_id, place_id)
    await callback.answer("Добавлено в избранное ❤️", show_alert=False)


@dp.callback_query(F.data.startswith("like:"))
async def like_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    save_user(user_id)

    place_id = callback.data.split(":", 1)[1]
    place = find_place_by_id(place_id)

    if not place:
        await callback.answer("Место не найдено", show_alert=True)
        return

    current_vote = get_vote_db(user_id, place_id)

    if current_vote == "like":
        await callback.answer("Ты уже поставил 👍")
        return

    set_vote_db(user_id, place_id, "like")

    await callback.message.edit_reply_markup(
        reply_markup=card_buttons(place)
    )
    await callback.answer("Ты поставил 👍")


@dp.callback_query(F.data.startswith("dislike:"))
async def dislike_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    save_user(user_id)

    place_id = callback.data.split(":", 1)[1]
    place = find_place_by_id(place_id)

    if not place:
        await callback.answer("Место не найдено", show_alert=True)
        return

    current_vote = get_vote_db(user_id, place_id)

    if current_vote == "dislike":
        await callback.answer("Ты уже поставил 👎")
        return

    set_vote_db(user_id, place_id, "dislike")

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
    USERS.add(message.from_user.id)
    save_user(message.from_user.id)
    await message.answer("Нажми /start и выбери кнопку из меню.")


async def main():
    init_db()
    me = await bot.get_me()
    print(f"BOT STARTED: @{me.username}", flush=True)
    await bot.delete_webhook(drop_pending_updates=True)
    print("WEBHOOK CLEARED", flush=True)
    print("POLLING", flush=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
