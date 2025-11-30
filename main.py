# main.py
import asyncio
import random
import os
import threading
import time
from flask import Flask
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ------------------- FLASK KEEP-ALIVE -------------------
flask_app = Flask('')

@flask_app.route('/')
def home():
    return "I'm alive"

def start_flask():
    try:
        flask_app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Flask error: {e}")

REQUIRED_CHANNELS = [
    {"id": "@domclaren", "name": "domclaren", "url": "https://t.me/domclaren"},
    {"id": "@boysssk", "name": "boysssk", "url": "https://t.me/boysssk"},
    {"id": "-1002065926656", "name": "Канал 2", "url": "https://t.me/+Y2oggP2OdmxkZjUy"},
    {"id": "-1001850202769", "name": "Канал", "url": "https://t.me/+uL7_MQDWrohhZmY6"},
]

async def check_subscription(user_id: int) -> list:
    not_subscribed = []
    for channel in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel["id"], user_id=user_id)
            if member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]:
                not_subscribed.append(channel)
        except Exception as e:
            print(f"Ошибка проверки канала {channel['name']}: {e}")
            not_subscribed.append(channel)
    return not_subscribed

def subscribe_kb(channels: list) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=f"Подписаться на {ch['name']}", url=ch["url"])] for ch in channels]
    rows.append([InlineKeyboardButton(text="Проверить подписку", callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

# ------------------- ТЕМЫ -------------------
THEMES = {
    "locations": {
        "name": "Локации",
        "items": [
            "Каток в Коломне", "Thialf Херенвен", "Utah Olympic Oval", "Медео", "Адлер-Арена", "Salt Lake City" , "Calgary"
            "Старт на 500 м", "Комната заточки коньков", "Подиум", "Заливочная машина",
            "Разминочная дорожка", "Трибуны во время масс-старта", "Судейская"
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
            "Карась (Благодастких)", "Малой (Васев)", "Румпель", "Юрец Алларт", "Клименков",
            "Свиридов", "Кондратьев", "Денчик (Лукин)", "Армения (Арман)", "Заеба (Засоба)",
            "Варя Никитина", "Варя Коновалова", "Саша Лазарев", "Тима Игнатьев", "Тёма Розин", "Артем Кузнецов",
            "Севас Гурин", "Денчик Бойков", "Леврен", "Саша Кириченко", "Федя Романов", "Гусь (Гуслинский)",
            "Костян Кураков", "Егорка Щеглов", "Егор Горячев", "Егорыч (Егор Леонидович)", "Ирина Мирская", "кот (косыныч)",
            "панч", "броник (бронеслав)", "Артем Снетков", "Чуриков Кирилл", "Шерр Миша",
            "Славик Воробьев", "Владос Пострел", "Иннокентий", "Гончаров Жека", "Катя Чернухина",
            "Жека мудак Жаров", "Матвей Нейдек", "Шабан Мусаев", "Илюха Иванов)))", "Вика Сичинава",
            "Тима Соболев", "мс кальмар (андрюха шукшин)", "Ульяна Гущина", "Янчик", "Спица",
            "Даша Савельева (легенда)", "Дима Стенин", "Стас Подоров", "Надя Чурсина",
            "Виктор Лобас", "Чепик Ванёк", "Бартылев Артем"
        ]
    },
    "russia": {
        "name": "Конькобежцы России",
        "items": [
            "Карамов Тимур",
            "Арефьев Артем",
            "Мурашов Руслан",
            "Муштаков Виктор",
            "Трофимов Сергей",
            "Алдошкин Даниил",
            "Румпель (одаа)",
            "Павел Кулижников",
            "Ольга Фаткулина",
            "Дарья Качанова",
            "Найденышев Даниил",
            "Фруктов Иван"
        ]
    },
    "holes": {
        "name": "Дырки катка",
        "items": None  # специально None
    }
}

active_games = {}
bot_users = set()
USERS_FILE = "users.txt"

def log_user(user_id: int, username: str, full_name: str):
    """Логирует пользователя в файл"""
    try:
        with open(USERS_FILE, "a", encoding="utf-8") as f:
            f.write(f"ID: {user_id} | Username: @{username} | Имя: {full_name}\n")
    except Exception as e:
        print(f"Ошибка при логировании пользователя: {e}")

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

def players_buttons(chat_id: int, total: int, show_finish: bool = False) -> InlineKeyboardMarkup:
    rows = []
    for i in range(1, total + 1):
        text = f"Я игрок {i}"
        rows.append([InlineKeyboardButton(text=text, callback_data=f"role_{chat_id}_{i}")])
    rows.append([InlineKeyboardButton(text="Начать заново", callback_data=f"restart_{chat_id}")])
    if show_finish:
        rows.append([InlineKeyboardButton(text="бесполезная кнопка, мне лень убирать", callback_data=f"finish_{chat_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

# ------------------- СТАРТ -------------------
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "нет юзернейма"
    full_name = message.from_user.full_name
    bot_users.add(user_id)
    log_user(user_id, username, full_name)
    print(f"Пользователь: {full_name} (@{username}), ID: {user_id}. Всего уникальных: {len(bot_users)}")
    
    not_subscribed = await check_subscription(user_id)
    if not_subscribed:
        await message.answer(
            "Для использования бота подпишитесь на каналы:",
            reply_markup=subscribe_kb(not_subscribed)
        )
        return
    await message.answer("Привет! Это Шпион \nВыбери тему игры:", reply_markup=theme_kb())

@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(call: types.CallbackQuery):
    not_subscribed = await check_subscription(call.from_user.id)
    if not_subscribed:
        await call.answer("Вы не подписаны на все каналы!", show_alert=True)
        return
    await call.message.edit_text("Привет! Это Шпион \nВыбери тему игры:", reply_markup=theme_kb())

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
        await call.message.edit_text("в процессе)...", reply_markup=None)
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
        "По очереди нажимайте свою кнопку - после просмотра удалите сообщение с темой/шпионом.",
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
        text = "<b>ТЫ — ШПИОН!\n</b>Ты не знаешь, кто/что это - выведай у других!"
    else:
        text = f"<b>Это:</b>\n<code>{game['item']}</code>"

    hide_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Скрыть", callback_data="hide_role")]
    ])
    await bot.send_message(user_id, text, disable_notification=True, reply_markup=hide_kb)
    game["seen"].add(user_id)

    try:
        await call.message.edit_reply_markup(reply_markup=players_buttons(chat_id, game["total"], show_finish=True))
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            print(f"Ошибка при обновлении кнопок: {e}")
    await call.answer("Роль в личку!")

@dp.callback_query(F.data == "hide_role")
async def hide_role(call: types.CallbackQuery):
    await call.message.delete()

@dp.callback_query(F.data.startswith("restart_"))
async def restart_game(call: types.CallbackQuery):
    chat_id = int(call.data.split("_")[1])
    if chat_id in active_games:
        del active_games[chat_id]
    await call.message.edit_text("Выбери тему игры:", reply_markup=theme_kb())

@dp.callback_query(F.data.startswith("finish_"))
async def game_finish(call: types.CallbackQuery):
    chat_id = int(call.data.split("_")[1])
    if chat_id not in active_games:
        return
    game = active_games[chat_id]

    if len(game["seen"]) < game["total"]:
        await call.answer("привет)0))", show_alert=True)
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
    print("Шпион запущен")
    await dp.start_polling(bot, handle_signals=False)

# Запуск Flask сервера в отдельном потоке
threading.Thread(target=start_flask, daemon=True).start()
# Запуск бота в отдельном потоке
threading.Thread(target=asyncio.run, args=(main(),), daemon=True).start()
while True:
    time.sleep(60)
