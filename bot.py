# bot.py

import asyncio
import sqlite3
import requests
from urllib.parse import quote

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    CallbackQuery,
    BotCommand,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)

from deep_translator import GoogleTranslator

# ================= CONFIG =================

TOKEN = "8928016779:AAHkU4bBYzudQ_J3kDoSaTsds5iQ5-N0p1I"
TMDB_API_KEY = "630493a5834623cd0916f69e1eee201c"

bot = Bot(token=TOKEN)
dp = Dispatcher()

BASE = "https://api.themoviedb.org/3"
IMG = "https://image.tmdb.org/t/p/w500"

# ================= DATABASE =================

conn = sqlite3.connect("movies.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS favorites(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    title TEXT
)
""")

conn.commit()

# ================= MENU =================

menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎬 Kino qidirish")],
        [KeyboardButton(text="❤️ Favorites")],
        [KeyboardButton(text="ℹ️ Help")]
    ],
    resize_keyboard=True
)

# ================= START =================

@dp.message(CommandStart())
async def start(message: Message):

    text = (
        "🍿 UZBEK CINEMA BOT\n\n"
        "🎬 Kino qidiring\n"
        "❤️ Favorite saqlang\n"
        "▶ Trailer ko'ring\n"
        "🔎 Google orqali toping\n\n"
        "Menyudan tanlang 👇"
    )

    await message.answer(text, reply_markup=menu)

# ================= HELP =================

@dp.message(Command("help"))
async def help_cmd(message: Message):

    await message.answer(
        "/start - Bosh menyu\n"
        "/search - Kino qidirish\n"
        "/favorites - Sevimlilar\n"
        "/help - Yordam"
    )

# ================= SEARCH COMMAND =================

@dp.message(Command("search"))
async def search_cmd(message: Message):
    await message.answer("🎬 Kino nomini yuboring")

# ================= FAVORITES COMMAND =================

@dp.message(Command("favorites"))
async def favorites_cmd(message: Message):

    cur.execute(
        "SELECT title FROM favorites WHERE user_id=?",
        (str(message.from_user.id),)
    )

    rows = cur.fetchall()

    if not rows:
        return await message.answer("❌ Favorites bo'sh")

    txt = "❤️ Sevimli kinolar:\n\n"

    for i, row in enumerate(rows, start=1):
        txt += f"{i}. {row[0]}\n"

    await message.answer(txt)

# ================= CALLBACK =================

@dp.callback_query()
async def callback(call: CallbackQuery):

    if call.data.startswith("fav|"):

        title = call.data.split("|", 1)[1]

        cur.execute(
            "INSERT INTO favorites(user_id,title) VALUES(?,?)",
            (str(call.from_user.id), title)
        )

        conn.commit()

        await call.answer("❤️ Favorite saqlandi", show_alert=True)

# ================= MAIN SEARCH =================

@dp.message()
async def movie_search(message: Message):

    text = message.text.strip()

    if text == "🎬 Kino qidirish":
        return await message.answer("🎬 Kino nomini yozing")

    if text == "❤️ Favorites":
        return await favorites_cmd(message)

    if text == "ℹ️ Help":
        return await help_cmd(message)

    url = (
        f"{BASE}/search/movie"
        f"?api_key={TMDB_API_KEY}"
        f"&language=uz-UZ"
        f"&query={quote(text)}"
    )

    try:
        res = requests.get(url, timeout=15).json()
    except:
        return await message.answer("❌ Server bilan aloqa yo'q")

    if not res.get("results"):

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔎 Google'dan qidirish",
                        url=f"https://www.google.com/search?q={quote(text + ' uzbek dublyaj')}"
                    )
                ]
            ]
        )

        return await message.answer(
            "❌ Kino topilmadi",
            reply_markup=kb
        )

    for movie in res["results"][:3]:

        title = movie.get("title", "Noma'lum")
        rating = movie.get("vote_average", "0")
        overview = movie.get("overview", "")
        poster = movie.get("poster_path")

        try:
            uz_title = GoogleTranslator(
                source="auto",
                target="uz"
            ).translate(title)
        except:
            uz_title = title

        try:
            uz_overview = GoogleTranslator(
                source="auto",
                target="uz"
            ).translate(overview[:300])
        except:
            uz_overview = overview

        trailer = (
            "https://www.youtube.com/results?search_query="
            + quote(title + " trailer")
        )

        watch = (
            "https://www.google.com/search?q="
            + quote(title + " uzbek dublyaj")
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="▶ Trailer",
                        url=trailer
                    ),
                    InlineKeyboardButton(
                        text="🎬 Ko'rish",
                        url=watch
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❤️ Favorite",
                        callback_data=f"fav|{title}"
                    )
                ]
            ]
        )

        caption = (
            f"🎬 {uz_title}\n"
            f"⭐ Reyting: {rating}\n\n"
            f"📝 {uz_overview[:250]}"
        )

        if poster:
            image_url = IMG + poster

            await message.answer_photo(
                photo=image_url,
                caption=caption,
                reply_markup=keyboard
            )
        else:
            await message.answer(
                caption,
                reply_markup=keyboard
            )

# ================= RUN =================

async def main():

    await bot.set_my_commands([
        BotCommand(
            command="start",
            description="🏠 Bosh menyu"
        ),
        BotCommand(
            command="search",
            description="🎬 Kino qidirish"
        ),
        BotCommand(
            command="favorites",
            description="❤️ Sevimlilar"
        ),
        BotCommand(
            command="help",
            description="ℹ️ Yordam"
        )
    ])

    print("🇺🇿 UZBEK CINEMA BOT ISHLADI")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

