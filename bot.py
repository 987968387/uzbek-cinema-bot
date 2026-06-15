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
        [KeyboardButton(text="📺 YouTube qidirish")],
        [KeyboardButton(text="❤️ Saqlanganlar")],
        [KeyboardButton(text="ℹ️ Help")]
    ],
    resize_keyboard=True
)

# ================= START =================

@dp.message(CommandStart())
async def start(message: Message):

    await message.answer(
        "🍿 UZBEK CINEMA BOT\n\n"
        "🎬 Kino qidiring\n"
        "📺 YouTube qidiring\n"
        "❤️ Saqlanganlar\n"
        "Menyudan tanlang 👇",
        reply_markup=menu
    )

# ================= HELP =================

@dp.message(Command("help"))
async def help_cmd(message: Message):

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👨‍💻 Admin bilan bog'lanish",
                    url="https://t.me/YOUR_USERNAME"
                )
            ]
        ]
    )

    await message.answer(
        "🆘 Yordam\n\n"
        "🎬 Kino qidirish\n"
        "📺 YouTube qidirish\n"
        "❤️ Saqlanganlar\n",
        reply_markup=kb
    )

# ================= FAVORITES =================

@dp.message(Command("favorites"))
async def favorites_cmd(message: Message):

    cur.execute(
        "SELECT title FROM favorites WHERE user_id=?",
        (str(message.from_user.id),)
    )

    rows = cur.fetchall()

    if not rows:
        return await message.answer("❌ Saqlangan kinolar yo‘q")

    text = "❤️ Saqlangan kinolar:\n\n"

    for i, row in enumerate(rows, start=1):
        text += f"{i}. {row[0]}\n"

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗑 Barchasini o‘chirish",
                    callback_data="clear_fav"
                )
            ]
        ]
    )

    await message.answer(text, reply_markup=kb)

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

        await call.answer("❤️ Saqlandi", show_alert=True)

    elif call.data == "clear_fav":

        cur.execute(
            "DELETE FROM favorites WHERE user_id=?",
            (str(call.from_user.id),)
        )

        conn.commit()

        await call.message.edit_text("🗑 Hammasi o‘chirildi")

# ================= MAIN =================

@dp.message()
async def movie_search(message: Message):

    text = message.text.strip()

    # MENU FIX
    if text == "🎬 Kino qidirish":
        return await message.answer("🎬 Kino nomini yozing")

    if text == "📺 YouTube qidirish":
        return await message.answer(
            "📺 YouTube qidirish uchun kino nomini yozing"
        )

    if text == "❤️ Saqlanganlar":
        return await favorites_cmd(message)

    if text == "ℹ️ Help":
        return await help_cmd(message)

    # ================= TMDB SEARCH =================

    url = (
        f"{BASE}/search/movie"
        f"?api_key={TMDB_API_KEY}"
        f"&language=uz-UZ"
        f"&query={quote(text)}"
    )

    try:
        res = requests.get(url, timeout=15).json()
    except:
        return await message.answer("❌ Internet xato")

    # ================= NOT FOUND =================

    if not res.get("results"):

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔎 Google",
                        url=f"https://www.google.com/search?q={quote(text)}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📺 YouTube",
                        url=f"https://www.youtube.com/results?search_query={quote(text + ' kino')}"
                    )
                ]
            ]
        )

        return await message.answer(
            "❌ Kino topilmadi\n\nGoogle yoki YouTube'da qidiring 👇",
            reply_markup=kb
        )

    # ================= SHOW RESULTS =================

    for movie in res["results"][:3]:

        title = movie.get("title", "Noma'lum")
        rating = movie.get("vote_average", "0")
        overview = movie.get("overview", "")
        poster = movie.get("poster_path")

        trailer = "https://www.youtube.com/results?search_query=" + quote(title + " trailer")
        watch = "https://www.google.com/search?q=" + quote(title)

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="▶ Trailer", url=trailer),
                    InlineKeyboardButton(text="🎬 Ko‘rish", url=watch)
                ],
                [
                    InlineKeyboardButton(
                        text="❤️ Saqlash",
                        callback_data=f"fav|{title}"
                    )
                ]
            ]
        )

        caption = f"🎬 {title}\n⭐ Reyting: {rating}\n\n📝 {overview[:200]}"

        if poster:
            await message.answer_photo(
                IMG + poster,
                caption=caption,
                reply_markup=keyboard
            )
        else:
            await message.answer(caption, reply_markup=keyboard)

# ================= RUN =================

async def main():

    await bot.set_my_commands([
        BotCommand(command="start", description="🏠 Menu"),
        BotCommand(command="favorites", description="❤️ Saqlanganlar"),
        BotCommand(command="help", description="ℹ️ Help")
    ])

    print("BOT ISHLADI...")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
