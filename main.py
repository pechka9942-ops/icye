# main.py
import asyncio
import random
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ------------------- ТЕМЫ -------------------
THEMES = {
    "locations": {
        "name": "Конькобежный спорт (локации)",
        "items": [
            "Овал в Коломне", "Thialf Херенвен", "Utah Olympic Oval", "Медео", "Адлер-Арена",
            "Стартовая колодка 500 м", "Комната заточки коньков", "Подиум", "Заливочная машина",
            "Разминочный каток", "Трибуны во время масс-старта", "Судейская вышка"
        ]
    },
    "foreign": {
        "name": "Иностранные конькобежцы",
        "items": [
            "Nils van der Poel (Швеция)",
            "Patrick Roest (Нидерланды)",
            "Jutta Monica Leerdam (Нидерланды)",
            "Sven Kramer (Нидерланды)",
            "Femke Kok (Нидерланды)",
            "Jenning de Boo (Нидерланды)",
            "Jordan Stolz (США)",
            "Kjeld Nuis (Нидерланды)"
        ]
    },
    "local": {
        "name": "Местные легенды",
        "items": [
            "карась (благодастких)", "малой (васев)", "румпель", "юрец алларт", "клименков",
            "свиридов", "кондратьев", "денчик (лукин)", "армения (арман)", "заеба (засоба)",
            "варя никитина", "коновалова", "лазарев", "игнатьев", "розин", "кузнецов",
            "севас гурин", "денчик бойков", "леврен", "кириченко", "романов", "гусь (гуслинский)",
            "кураков", "щеглов", "горячев", "егорыч васин", "мирская", "кот (косыныч)",
            "панч", "броник (бронеслав)", "снетков", "чуриков кирилл", "шерр миша",
            "славик воробьев", "владос пострел", "иннокентий", "гончаров жека", "катя чернухина",
            "жека мудак жаров", "нейдек", "шабанов", "илюха иванов)))", "вика сичинава",
            "тима соболев", "мс кальмар (андрюха шукшин)", "ульяна гущина", "янчик", "спица",
            "даша савельева (легенда)", "дима стенин", "стас подоров", "надя чурсина",
            "витёк лобас", "чепик ванёк", "бартылев артем"
        ]
    },
    "holes": {
        "name": "Дырки катка",
        "items": None  # специально None
    }
}

active_games = {}

class States(StatesGroup):
    choosing_players = State()

# ------------------- КНОПКИ -------------------
def theme_kb():
    kb = [[InlineKeyboardButton(text=v["name"], callback_data=f"theme_{k}")] for k, v in THEMES.items()]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def players_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{i} игроков", callback_data=f"players_{i}") for i in range(3, 9)],
        [InlineKeyboardButton(text=f"{i} игроков", callback_data=f"players_{i}") for i in range(9, 13)]
    ])

def players_buttons(chat_id: int, total: int) -> InlineKeyboardMarkup:
    rows = []
    for i in range(1, total + 1):
        text = f"Я игрок {i}"
        rows.append([InlineKeyboardButton(text=text, callback_data=f"role_{chat_id}_{i}")])
    rows.append([InlineKeyboardButton(text="Готово — все посмотрели", callback_data=f"finish_{chat_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

# ------------------- СТАРТ -------------------
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("Привет! Это Шпион 2.0\nВыбери тему игры:", reply_markup=theme_kb())

@dp.callback_query(F.data.startswith("theme_"))
async def theme_selected(call: types.CallbackQuery, state: FSMContext):
    theme_key = call.data.split("_")[1]
    await state.update_data(theme=theme_key)
    await call.message.edit_text(
        f"<b>Тема:</b> {THEMES[theme_key]['name']}\n\nСколько будет игроков?",
        reply_markup=players_kb()
    )
    await state.set_state(States.choosing_players)

@dp.callback_query(F.data.startswith("players_"), States.choosing_players)
async def players_selected(call: types.CallbackQuery, state: FSMContext):
    total = int(call.data.split("_")[1])
    chat_id = call.message.chat.id
    data = await state.get_data()
    theme_key = data["theme"]

    if theme_key == "holes":
        await call.message.edit_text("в процессе...", reply_markup=None)
        await state.clear()
        return

    item = random.choice(THEMES[theme_key]["items"])
    spy_num = random.randint(1, total)

    active_games[chat_id] = {
        "total": total,
        "seen": set(),
        "item": item,
        "spy": spy_num,
        "theme": theme_key
    }

    await state.clear()
    await call.message.edit_text(
        f"<b>Игра началась!</b>\nТема: {THEMES[theme_key]['name']}\nИгроков: {total}\n\n"
        "По очереди нажимайте свою кнопку — роль придёт в личку.\n"
        "Когда все посмотрели — нажмите «Готово».",
        reply_markup=players_buttons(chat_id, total)
    )

@dp.callback_query(F.data.startswith("role_"))
async def show_role(call: types.CallbackQuery):
    _, chat_id, num = call.data.split("_")
    chat_id, num = int(chat_id), int(num)
    user_id = call.from_user.id

    if chat_id not in active_games:
        return
    game = active_games[chat_id]

    is_spy = (num == game["spy"])
    if is_spy:
        text = "<b>ТЫ — ШПИОН!\n</b>Ты не знаешь, кто/что это — выведай у других!"
    else:
        text = f"<b>Это:</b>\n<code>{game['item']}</code>"

    await bot.send_message(user_id, text, disable_notification=True)
    game["seen"].add(user_id)

    await call.message.edit_reply_markup(reply_markup=players_buttons(chat_id, game["total"]))
    await call.answer("Роль в личку!")

@dp.callback_query(F.data.startswith("finish_"))
async def game_finish(call: types.CallbackQuery):
    chat_id = int(call.data.split("_")[1])
    if chat_id not in active_games:
        return
    game = active_games[chat_id]

    if len(game["seen"]) < game["total"]:
        await call.answer("Ещё не все посмотрели!", show_alert=True)
        return

    await call.message.edit_text(
        f"<b>Всё! Обсуждение началось!</b>\n\n"
        f"Это был: <code>{game['item']}</code>\n"
        f"Шпионом был игрок №<b>{game['spy']}</b>\n\n"
        "Новая игра — /start",
        reply_markup=None
    )
    del active_games[chat_id]

# ------------------- ДЛЯ RENDER -------------------
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    print("Шпион 2.0 запущен!")
    await dp.start_polling(bot, handle_signals=False)

import threading, time
threading.Thread(target=asyncio.run, args=(main(),), daemon=True).start()
while True:
    time.sleep(60)

# ←←← ЭТО ДОБАВЬ В САМЫЙ КОНЕЦ ФАЙЛА main.py (после всего кода) ←←←
import threading
import time
import uvicorn
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "alive"}

def run_web():
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

# Запускаем и веб-сервер (для Render), и бота одновременно
threading.Thread(target=run_web, daemon=True).start()

# ←←← Твой обычный запуск бота остаётся без изменений
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    print("Бот запущен 24/7")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
