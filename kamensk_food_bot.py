import os
import json
import asyncio
import random
from typing import Any, Optional

import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
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
PLACES_JSON_PATH = os.getenv("PLACES_JSON_PATH", "places.json")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

BOT_USERNAME: Optional[str] = None
USER_CONTEXT: dict[int, dict[str, Any]] = {}

ADS = [
    "📢 <b>Реклама</b>\n\nХочешь продвинуть своё заведение в боте? Напиши администратору.",
    "📢 <b>Реклама</b>\n\nПартнёрские места получают приоритет в подборках и отдельные промо-блоки.",
    "📢 <b>Реклама</b>\n\nЭтот бот можно использовать как городской food-гид. Для размещения — свяжись с владельцем.",
]


class OrderStates(StatesGroup):
    waiting_items = State()
    waiting_name = State()
    waiting_phone = State()
    waiting_mode = State()
    waiting_address = State()
    waiting_comment = State()


class SmartStates(StatesGroup):
    waiting_budget = State()
    waiting_format = State()
    waiting_food = State()
    waiting_distance = State()


def load_places_from_json() -> dict[str, list[dict[str, Any]]]:
    with open(PLACES_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def all_places_list() -> list[dict[str, Any]]:
    data = load_places_from_json()
    result: list[dict[str, Any]] = []
    for items in data.values():
        result.extend(items)
    return result


def get_place_category(place_id: str) -> Optional[str]:
    data = load_places_from_json()
    for category, items in data.items():
        for place in items:
            if place["id"] == place_id:
                return category
    return None


def find_place_by_id(place_id: str) -> Optional[dict[str, Any]]:
    for place in all_places_list():
        if place["id"] == place_id:
            return place
    return None


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                user_id INTEGER,
                place_id TEXT,
                PRIMARY KEY (user_id, place_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS votes (
                user_id INTEGER,
                place_id TEXT,
                vote TEXT,
                PRIMARY KEY (user_id, place_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS partners (
                place_id TEXT PRIMARY KEY,
                is_partner INTEGER NOT NULL DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS analytics (
                metric TEXT PRIMARY KEY,
                value INTEGER NOT NULL DEFAULT 0
            )
        """)
        await db.execute("""
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
        await db.execute("""
            CREATE TABLE IF NOT EXISTS order_drafts (
                user_id INTEGER PRIMARY KEY,
                place_id TEXT,
                place_name TEXT,
                items TEXT,
                customer_name TEXT,
                phone TEXT,
                mode TEXT,
                address TEXT,
                comment TEXT,
                step TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def save_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        await db.commit()


async def get_all_users() -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cur:
            rows = await cur.fetchall()
    return [row[0] for row in rows]


async def add_favorite_db(user_id: int, place_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO favorites (user_id, place_id) VALUES (?, ?)",
            (user_id, place_id)
        )
        await db.commit()


async def get_favorites_db(user_id: int) -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT place_id FROM favorites WHERE user_id = ?", (user_id,)) as cur:
            rows = await cur.fetchall()
    return [row[0] for row in rows]


async def get_vote_db(user_id: int, place_id: str) -> Optional[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT vote FROM votes WHERE user_id = ? AND place_id = ?",
            (user_id, place_id)
        ) as cur:
            row = await cur.fetchone()
    return row[0] if row else None


async def set_vote_db(user_id: int, place_id: str, vote: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO votes (user_id, place_id, vote)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, place_id) DO UPDATE SET vote = excluded.vote
        """, (user_id, place_id, vote))
        await db.commit()


async def count_votes_db(place_id: str) -> tuple[int, int]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM votes WHERE place_id = ? AND vote = 'like'",
            (place_id,)
        ) as cur:
            up = (await cur.fetchone())[0]

        async with db.execute(
            "SELECT COUNT(*) FROM votes WHERE place_id = ? AND vote = 'dislike'",
            (place_id,)
        ) as cur:
            down = (await cur.fetchone())[0]

    return up, down


async def set_partner_db(place_id: str, is_partner: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO partners (place_id, is_partner)
            VALUES (?, ?)
            ON CONFLICT(place_id) DO UPDATE SET is_partner = excluded.is_partner
        """, (place_id, 1 if is_partner else 0))
        await db.commit()


async def get_partners_map() -> dict[str, bool]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT place_id, is_partner FROM partners") as cur:
            rows = await cur.fetchall()
    return {place_id: bool(is_partner) for place_id, is_partner in rows}


async def inc_metric(name: str, value: int = 1):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO analytics (metric, value)
            VALUES (?, ?)
            ON CONFLICT(metric) DO UPDATE SET value = value + excluded.value
        """, (name, value))
        await db.commit()


async def get_metric(name: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM analytics WHERE metric = ?", (name,)) as cur:
            row = await cur.fetchone()
    return int(row[0]) if row else 0


async def get_metrics_map() -> dict[str, int]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT metric, value FROM analytics") as cur:
            rows = await cur.fetchall()
    return {metric: int(value) for metric, value in rows}


async def save_order_db(data: dict[str, Any]):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
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
        await db.commit()


async def get_recent_orders(limit: int = 10) -> list[tuple]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT id, place_name, customer_name, phone, status, created_at
            FROM orders
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)) as cur:
            rows = await cur.fetchall()
    return rows


async def save_order_draft(user_id: int, data: dict[str, Any]):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO order_drafts (
                user_id, place_id, place_name, items, customer_name, phone,
                mode, address, comment, step, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                place_id=excluded.place_id,
                place_name=excluded.place_name,
                items=excluded.items,
                customer_name=excluded.customer_name,
                phone=excluded.phone,
                mode=excluded.mode,
                address=excluded.address,
                comment=excluded.comment,
                step=excluded.step,
                updated_at=CURRENT_TIMESTAMP
        """, (
            user_id,
            data.get("place_id"),
            data.get("place_name"),
            data.get("items"),
            data.get("customer_name"),
            data.get("phone"),
            data.get("mode"),
            data.get("address"),
            data.get("comment"),
            data.get("step"),
        ))
        await db.commit()


async def delete_order_draft(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM order_drafts WHERE user_id = ?", (user_id,))
        await db.commit()


async def apply_partner_flags_from_db():
    partners_map = await get_partners_map()
    data = load_places_from_json()
    changed = False

    for _, items in data.items():
        for place in items:
            pid = place["id"]
            if pid in partners_map and place.get("is_partner") != partners_map[pid]:
                place["is_partner"] = partners_map[pid]
                changed = True

    if changed:
        with open(PLACES_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


async def track_place_view(place_id: str):
    await inc_metric(f"view_place:{place_id}")
    category = get_place_category(place_id)
    if category:
        await inc_metric(f"view_category:{category}")


async def get_place_views(place_id: str) -> int:
    return await get_metric(f"view_place:{place_id}")


async def get_total_views() -> int:
    total = 0
    for place in all_places_list():
        total += await get_place_views(place["id"])
    return total


def format_place(place: dict[str, Any]) -> str:
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


def format_order_request(data: dict[str, Any]) -> str:
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


async def popularity_score(place: dict[str, Any]) -> int:
    up, down = await count_votes_db(place["id"])
    views = await get_place_views(place["id"])
    partner_bonus = 3 if place.get("is_partner", False) else 0
    return (up * 3) - (down * 2) + views + partner_bonus


async def sort_places_by_score(places: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched = []
    for place in places:
        score = await popularity_score(place)
        votes = await count_votes_db(place["id"])
        enriched.append((place, score, votes))

    enriched.sort(
        key=lambda item: (item[0].get("is_partner", False), item[1], item[2][0]),
        reverse=True,
    )
    return [item[0] for item in enriched]


def smart_filter_places(
    budget: Optional[str] = None,
    fmt: Optional[str] = None,
    food: Optional[str] = None,
    distance: Optional[str] = None,
    night_only: bool = False,
) -> list[dict[str, Any]]:
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
    return result


async def get_most_popular_places(limit: int = 5) -> list[dict[str, Any]]:
    return (await sort_places_by_score(all_places_list()))[:limit]


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
        keyboard=[[KeyboardButton(text="❌ Отменить заказ")]],
        resize_keyboard=True
    )


def get_more_keyboard(cursor_key: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Ещё 5 мест", callback_data=f"more:{cursor_key}")]
        ]
    )


async def card_buttons(place: dict[str, Any]) -> InlineKeyboardMarkup:
    up, down = await count_votes_db(place["id"])
    share_url = (
        f"https://t.me/share/url?url={build_share_url()}"
        f"&text=Смотри, нашёл бота где можно выбрать место поесть в Каменске"
    )

    rows = [[InlineKeyboardButton(text="📍 Открыть в Яндекс Картах", url=place["url"])]]

    if place.get("is_partner", False):
        rows.append([InlineKeyboardButton(text="🛒 Оставить заказ", callback_data=f"order:{place['id']}")])

    rows.extend([
        [InlineKeyboardButton(text="❤️ В избранное", callback_data=f"fav:{place['id']}")],
        [
            InlineKeyboardButton(text=f"👍 {up}", callback_data=f"like:{place['id']}"),
            InlineKeyboardButton(text=f"👎 {down}", callback_data=f"dislike:{place['id']}"),
        ],
        [InlineKeyboardButton(text="📤 Поделиться ботом", url=share_url)],
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


async def send_place_card(message: Message, place: dict[str, Any]):
    await track_place_view(place["id"])
    await message.answer(
        format_place(place),
        parse_mode="HTML",
        reply_markup=await card_buttons(place),
    )


async def send_ad_block(message: Message):
    await message.answer(random.choice(ADS), parse_mode="HTML")


async def send_places_with_ad(message: Message, places: list[dict[str, Any]], title: Optional[str] = None, limit: int = 5):
    if title:
        await message.answer(title, reply_markup=get_back_keyboard())

    if not places:
        await message.answer("Пока ничего не найдено.", reply_markup=get_back_keyboard())
        return

    key = message.from_user.id
    USER_CONTEXT[key] = {"places": places, "offset": 0}

    for place in places[:limit]:
        await send_place_card(message, place)

    USER_CONTEXT[key]["offset"] = limit

    if len(places) > limit:
        await message.answer(
            "Показал первые места. Нажми, чтобы увидеть ещё:",
            reply_markup=get_more_keyboard(str(key))
        )

    await send_ad_block(message)


async def format_admin_stats() -> str:
    metrics = await get_metrics_map()
    users_count = len(await get_all_users())
    places_count = len(all_places_list())
    partners_count = len([p for p in all_places_list() if p.get("is_partner", False)])

    likes = 0
    dislikes = 0
    for place in all_places_list():
        up, down = await count_votes_db(place["id"])
        likes += up
        dislikes += down

    views = await get_total_views()
    top_places = await get_most_popular_places(5)
    orders = await get_recent_orders(1000)

    lines = [
        "📊 <b>Статистика бота</b>",
        "",
        f"👥 Пользователей: {users_count}",
        f"📍 Всего заведений: {places_count}",
        f"🤝 Партнёров: {partners_count}",
        f"👀 Просмотров карточек: {views}",
        f"🛒 Заявок: {len(orders)}",
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
        "🔥 <b>Топ-5 популярных мест:</b>",
    ]

    if not top_places:
        lines.append("Пока нет данных.")
    else:
        for i, place in enumerate(top_places, start=1):
            up, down = await count_votes_db(place["id"])
            views_place = await get_place_views(place["id"])
            lines.append(f"{i}. {place['name']} (👍 {up} / 👎 {down} / 👀 {views_place})")

    return "\n".join(lines)


@dp.message(CommandStart())
async def start_handler(message: Message):
    await save_user(message.from_user.id)
    await inc_metric("start_used")
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
    await message.answer(await format_admin_stats(), parse_mode="HTML")


@dp.message(Command("users"))
async def admin_users(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        f"👥 Пользователей в базе: <b>{len(await get_all_users())}</b>",
        parse_mode="HTML"
    )


@dp.message(Command("partners"))
async def admin_partners(message: Message):
    if not is_admin(message.from_user.id):
        return

    partners = [p for p in all_places_list() if p.get("is_partner", False)]
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

    orders = await get_recent_orders(10)
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

    success = 0
    failed = 0
    for user_id in await get_all_users():
        try:
            await bot.send_message(
                user_id,
                f"📢 <b>Обновление бота</b>\n\n{text}",
                parse_mode="HTML"
            )
            success += 1
        except Exception:
            failed += 1

    await message.answer(f"✅ Рассылка завершена\n\nУспешно: {success}\nНе доставлено: {failed}")


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

    await set_partner_db(place_id, True)
    await apply_partner_flags_from_db()
    await message.answer(f"✅ Партнёр включён: <b>{place['name']}</b>", parse_mode="HTML")


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

    await set_partner_db(place_id, False)
    await apply_partner_flags_from_db()
    await message.answer(f"❌ Партнёр выключен: <b>{place['name']}</b>", parse_mode="HTML")


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
    data = load_places_from_json()
    await send_places_with_ad(message, await sort_places_by_score(data["🍔 Бургеры"]), "🍔 Лучшие бургеры:")


@dp.message(F.text == "🌯 Топ шаурма")
async def top_shaurma(message: Message):
    data = load_places_from_json()
    await send_places_with_ad(message, await sort_places_by_score(data["🌯 Шаурма"]), "🌯 Лучшая шаурма:")


@dp.message(F.text == "🍕 Топ пицца")
async def top_pizza(message: Message):
    data = load_places_from_json()
    await send_places_with_ad(message, await sort_places_by_score(data["🍕 Пицца"]), "🍕 Лучшая пицца:")


@dp.message(F.text == "☕ Топ кофе")
async def top_coffee(message: Message):
    data = load_places_from_json()
    await send_places_with_ad(message, await sort_places_by_score(data["☕ Кофе"]), "☕ Лучший кофе:")


@dp.message(F.text == "🍺 Топ бары")
async def top_bars(message: Message):
    data = load_places_from_json()
    await send_places_with_ad(message, await sort_places_by_score(data["🍺 Бары"]), "🍺 Лучшие бары:")


@dp.message(F.text == "🔥 Сейчас популярно")
async def popular_handler(message: Message):
    await inc_metric("popular_used")
    await send_places_with_ad(message, await get_most_popular_places(20), "🔥 Сейчас популярно в боте:", limit=5)


@dp.message(F.text == "💑 Топ для свидания")
async def top_for_date_handler(message: Message):
    await inc_metric("top_date_used")
    await send_places_with_ad(
        message,
        await sort_places_by_score(smart_filter_places(fmt="💑 Свидание")),
        "💑 Лучшие места для свидания:",
        limit=5
    )


@dp.message(F.text == "💸 Топ до 500")
async def top_under_500_handler(message: Message):
    await inc_metric("top_budget_used")
    await send_places_with_ad(
        message,
        await sort_places_by_score(smart_filter_places(budget="💸 До 500")),
        "💸 Лучшие места до 500:",
        limit=5
    )


@dp.message(F.text == "👥 Топ для компании")
async def top_for_company_handler(message: Message):
    await inc_metric("top_company_used")
    await send_places_with_ad(
        message,
        await sort_places_by_score(smart_filter_places(fmt="👥 Компания")),
        "👥 Лучшие места для компании:",
        limit=5
    )


@dp.message(F.text == "🎯 Случайное по фильтру")
async def random_filter_menu_handler(message: Message):
    await message.answer("🎯 Выбери сценарий:", reply_markup=get_random_filter_keyboard())


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

    fast = await sort_places_by_score(fast)
    if not fast:
        await message.answer("Ничего не найдено.", reply_markup=get_back_keyboard())
        return

    await message.answer("🎲 Быстрый перекус:", reply_markup=get_back_keyboard())
    await send_place_card(message, random.choice(fast))


@dp.message(F.text == "🧠 Подобрать место")
async def smart_menu_handler(message: Message, state: FSMContext):
    await inc_metric("smart_used")
    await state.set_state(SmartStates.waiting_budget)
    await state.set_data({})
    await message.answer("🧠 Подберём место.\n\nСколько хочешь потратить?", reply_markup=get_budget_keyboard())


@dp.message(SmartStates.waiting_budget, F.text.in_(["💸 До 500", "💰 До 1000", "💎 Не важно"]))
async def smart_budget_handler(message: Message, state: FSMContext):
    await state.update_data(budget=message.text)
    await state.set_state(SmartStates.waiting_format)
    await message.answer("С кем идёшь?", reply_markup=get_format_keyboard())


@dp.message(SmartStates.waiting_format, F.text.in_(["👤 Один", "💑 Свидание", "👥 Компания"]))
async def smart_format_handler(message: Message, state: FSMContext):
    await state.update_data(fmt=message.text)
    await state.set_state(SmartStates.waiting_food)
    await message.answer("Что хочется по еде?", reply_markup=get_food_keyboard())


@dp.message(
    SmartStates.waiting_food,
    F.text.in_(["🍔 Бургеры", "🌯 Шаурма", "🍕 Пицца", "☕ Кофе", "🍺 Бары", "🍽 Не важно"])
)
async def smart_food_handler(message: Message, state: FSMContext):
    await state.update_data(food=message.text)
    await state.set_state(SmartStates.waiting_distance)
    await message.answer("Как по расстоянию?", reply_markup=get_distance_keyboard())


@dp.message(SmartStates.waiting_distance, F.text.in_(["🚶 Рядом", "🚕 Не важно"]))
async def smart_distance_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    result = smart_filter_places(
        budget=data.get("budget"),
        fmt=data.get("fmt"),
        food=data.get("food"),
        distance=message.text,
    )
    await state.clear()
    await send_places_with_ad(
        message,
        await sort_places_by_score(result),
        "🎯 Вот что лучше всего подходит тебе:",
        limit=5
    )


@dp.message(F.text.in_(["🍔 Бургеры", "🌯 Шаурма", "🍕 Пицца", "☕ Кофе", "🍺 Бары"]))
async def category_handler(message: Message, state: FSMContext):
    await state.clear()
    data = load_places_from_json()
    category = message.text
    await inc_metric(f"open_category:{category}")
    await send_places_with_ad(
        message,
        await sort_places_by_score(data[category]),
        f"{category} в Каменске-Уральском:",
        limit=5
    )


@dp.message(F.text == "⭐ Лучшие места")
async def top_handler(message: Message, state: FSMContext):
    await state.clear()
    await send_places_with_ad(
        message,
        (await sort_places_by_score(all_places_list()))[:20],
        "⭐ Топ заведений по мнению пользователей:",
        limit=5
    )


@dp.message(F.text == "🌙 Где поесть ночью")
async def night_handler(message: Message, state: FSMContext):
    await state.clear()
    await inc_metric("night_used")
    await send_places_with_ad(
        message,
        await sort_places_by_score(smart_filter_places(night_only=True)),
        "🌙 Где поесть ночью:",
        limit=5
    )


@dp.message(F.text == "🎲 Случайное место")
async def random_handler(message: Message, state: FSMContext):
    await state.clear()
    await inc_metric("random_used")
    place = random.choice(all_places_list())
    await message.answer("🎲 Сегодня попробуй:", reply_markup=get_back_keyboard())
    await send_place_card(message, place)


@dp.message(F.text == "❤️ Моё избранное")
async def favorites_handler(message: Message, state: FSMContext):
    await state.clear()
    await save_user(message.from_user.id)
    await inc_metric("favorites_used")

    favorite_ids = await get_favorites_db(message.from_user.id)
    if not favorite_ids:
        await message.answer("У тебя пока нет избранных мест.", reply_markup=get_back_keyboard())
        return

    places = [p for p in all_places_list() if p["id"] in favorite_ids]
    await send_places_with_ad(
        message,
        await sort_places_by_score(places),
        "❤️ Твоё избранное:",
        limit=5
    )


@dp.message(F.text == "💸 Дёшево")
async def cheap_handler(message: Message, state: FSMContext):
    await state.clear()
    await send_places_with_ad(
        message,
        await sort_places_by_score(smart_filter_places(budget="💸 До 500")),
        "💸 Недорогие варианты:",
        limit=5
    )


@dp.message(F.text == "⚡ Быстро")
async def fast_handler(message: Message, state: FSMContext):
    await state.clear()
    result = []
    for place in all_places_list():
        text = (place["name"] + " " + place["desc"]).lower()
        if any(word in text for word in ["шаурма", "бургер", "стритфуд", "фастфуд", "перекус"]):
            result.append(place)

    await send_places_with_ad(
        message,
        await sort_places_by_score(result),
        "⚡ Быстрый перекус:",
        limit=5
    )


@dp.message(F.text == "☕ Посидеть")
async def chill_handler(message: Message, state: FSMContext):
    await state.clear()
    result = [p for p in all_places_list() if p.get("food_type") in ["☕ Кофе", "🍺 Бары"]]
    await send_places_with_ad(
        message,
        await sort_places_by_score(result),
        "☕ Где можно посидеть:",
        limit=5
    )


@dp.callback_query(F.data.startswith("order:"))
async def start_order_handler(callback: CallbackQuery, state: FSMContext):
    place_id = callback.data.split(":", 1)[1]
    place = find_place_by_id(place_id)

    if not place:
        await callback.answer("Заведение не найдено", show_alert=True)
        return

    if not place.get("is_partner", False):
        await callback.answer("Заказ доступен только у партнёров", show_alert=True)
        return

    payload = {
        "user_id": callback.from_user.id,
        "place_id": place["id"],
        "place_name": place["name"],
        "step": "items",
    }

    await save_order_draft(callback.from_user.id, payload)
    await state.set_state(OrderStates.waiting_items)
    await state.set_data(payload)
    await inc_metric("order_started")

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
    await save_user(callback.from_user.id)
    place_id = callback.data.split(":", 1)[1]
    place = find_place_by_id(place_id)

    if not place:
        await callback.answer("Место не найдено", show_alert=True)
        return

    favorite_ids = await get_favorites_db(callback.from_user.id)
    if place_id in favorite_ids:
        await callback.answer("Уже в избранном ❤️")
        return

    await add_favorite_db(callback.from_user.id, place_id)
    await callback.answer("Добавлено в избранное ❤️")


@dp.callback_query(F.data.startswith("like:"))
async def like_handler(callback: CallbackQuery):
    await save_user(callback.from_user.id)
    place_id = callback.data.split(":", 1)[1]
    place = find_place_by_id(place_id)

    if not place:
        await callback.answer("Место не найдено", show_alert=True)
        return

    if await get_vote_db(callback.from_user.id, place_id) == "like":
        await callback.answer("Ты уже поставил 👍")
        return

    await set_vote_db(callback.from_user.id, place_id, "like")
    await callback.message.edit_reply_markup(reply_markup=await card_buttons(place))
    await callback.answer("Ты поставил 👍")


@dp.callback_query(F.data.startswith("dislike:"))
async def dislike_handler(callback: CallbackQuery):
    await save_user(callback.from_user.id)
    place_id = callback.data.split(":", 1)[1]
    place = find_place_by_id(place_id)

    if not place:
        await callback.answer("Место не найдено", show_alert=True)
        return

    if await get_vote_db(callback.from_user.id, place_id) == "dislike":
        await callback.answer("Ты уже поставил 👎")
        return

    await set_vote_db(callback.from_user.id, place_id, "dislike")
    await callback.message.edit_reply_markup(reply_markup=await card_buttons(place))
    await callback.answer("Ты поставил 👎")


@dp.callback_query(F.data.startswith("more:"))
async def more_places_handler(callback: CallbackQuery):
    try:
        key = int(callback.data.split(":", 1)[1])
    except ValueError:
        await callback.answer("Ошибка")
        return

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
        await callback.message.answer("Показать ещё?", reply_markup=get_more_keyboard(str(key)))
    else:
        await callback.message.answer("✅ Это все найденные места.")

    await callback.answer()


@dp.message(F.text == "❌ Отменить заказ")
async def cancel_order_handler(message: Message, state: FSMContext):
    await state.clear()
    await delete_order_draft(message.from_user.id)
    await message.answer("❌ Заказ отменён.", reply_markup=get_main_keyboard())


@dp.message(OrderStates.waiting_items)
async def order_items_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    data["items"] = message.text.strip()
    data["step"] = "name"
    await save_order_draft(message.from_user.id, data)
    await state.set_data(data)
    await state.set_state(OrderStates.waiting_name)
    await message.answer("👤 Напиши своё имя:", reply_markup=get_cancel_order_keyboard())


@dp.message(OrderStates.waiting_name)
async def order_name_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    data["customer_name"] = message.text.strip()
    data["step"] = "phone"
    await save_order_draft(message.from_user.id, data)
    await state.set_data(data)
    await state.set_state(OrderStates.waiting_phone)
    await message.answer("📞 Напиши телефон для связи:", reply_markup=get_cancel_order_keyboard())


@dp.message(OrderStates.waiting_phone)
async def order_phone_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    data["phone"] = message.text.strip()
    data["step"] = "mode"
    await save_order_draft(message.from_user.id, data)
    await state.set_data(data)
    await state.set_state(OrderStates.waiting_mode)
    await message.answer("📦 Выбери способ получения:", reply_markup=get_order_mode_keyboard())


@dp.message(OrderStates.waiting_mode)
async def order_mode_handler(message: Message, state: FSMContext):
    if message.text not in ["🚚 Доставка", "🏃 Самовывоз"]:
        await message.answer("Выбери один из вариантов: доставка или самовывоз.")
        return

    data = await state.get_data()
    data["mode"] = message.text

    if message.text == "🚚 Доставка":
        data["step"] = "address"
        await save_order_draft(message.from_user.id, data)
        await state.set_data(data)
        await state.set_state(OrderStates.waiting_address)
        await message.answer("📍 Напиши адрес доставки:", reply_markup=get_cancel_order_keyboard())
        return

    data["address"] = "Самовывоз"
    data["step"] = "comment"
    await save_order_draft(message.from_user.id, data)
    await state.set_data(data)
    await state.set_state(OrderStates.waiting_comment)
    await message.answer(
        "📝 Напиши комментарий к заказу или отправь '-' если без комментария:",
        reply_markup=get_cancel_order_keyboard()
    )


@dp.message(OrderStates.waiting_address)
async def order_address_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    data["address"] = message.text.strip()
    data["step"] = "comment"
    await save_order_draft(message.from_user.id, data)
    await state.set_data(data)
    await state.set_state(OrderStates.waiting_comment)
    await message.answer(
        "📝 Напиши комментарий к заказу или отправь '-' если без комментария:",
        reply_markup=get_cancel_order_keyboard()
    )


@dp.message(OrderStates.waiting_comment)
async def order_comment_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    data["comment"] = message.text.strip()

    try:
        await save_order_db(data)
        await bot.send_message(ADMIN_ID, format_order_request(data), parse_mode="HTML")
        await inc_metric("order_sent")
    except Exception:
        await message.answer(
            "⚠️ Не удалось отправить заявку. Попробуй позже.",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
        await delete_order_draft(message.from_user.id)
        return

    await state.clear()
    await delete_order_draft(message.from_user.id)
    await message.answer(
        "✅ Заявка отправлена.\n\nС тобой скоро свяжутся для подтверждения заказа.",
        reply_markup=get_main_keyboard()
    )


@dp.message(F.text == "⬅️ Назад")
async def back_handler(message: Message, state: FSMContext):
    await state.clear()
    await delete_order_draft(message.from_user.id)
    await message.answer(
        "🍴 Снова главное меню\n\nВыбери категорию:",
        reply_markup=get_main_keyboard()
    )


@dp.message()
async def fallback_handler(message: Message):
    await save_user(message.from_user.id)
    await message.answer(
        "Нажми /start и выбери кнопку из меню.",
        reply_markup=get_main_keyboard()
    )


async def main():
    global BOT_USERNAME

    await init_db()
    await apply_partner_flags_from_db()

    me = await bot.get_me()
    BOT_USERNAME = me.username

    print(f"BOT STARTED: @{me.username}", flush=True)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
