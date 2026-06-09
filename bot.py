import asyncio
import logging
import aiosqlite
from datetime import datetime, timedelta, date
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ================== НАСТРОЙКИ ==================
BOT_TOKEN = "8864864338:AAHHrRUz-yKRv4IeLqzwrktAOhtvXeKg50U"
ADMIN_IDS = [5904432161, 5135479321]

OWNER_USERNAME = "undertaker_86_5"

HOTEL_NAME = "Гостевой дом Белые скалы"
OWNER_NAME = "Наринэ Жорьевна"
ADDRESS = "Октябрьская улица, 40, поселок Гантиади, Автономная Республика Абхазия"
MAP_LINK = "https://yandex.com/maps/-/CPT2UTnU"
PHONE = "+7 (999) 655-73-27"
DESCRIPTION = (
    "🌊 Уютный гостевой дом в 5 минутах от моря.\n"
    "🛏️ 6 номеров с кондиционерами и Wi-Fi, балконами, кухней (общей уличной).\n"
    "🅿️ Бесплатная парковка."
)

ROOMS = [
    {"id": 1, "name": "1️⃣ Эконом 2-местный", "price": 1500, "capacity": 2, "extra_bed": False, "extra_bed_price": 0},
    {"id": 2, "name": "2️⃣ Стандарт 3-местный", "price": 2500, "capacity": 3, "extra_bed": True, "extra_bed_price": 0},
    {"id": 3, "name": "3️⃣ Стандарт 3-местный", "price": 2500, "capacity": 3, "extra_bed": True, "extra_bed_price": 0},
    {"id": 4, "name": "4️⃣ Стандарт 2-местный", "price": 2500, "capacity": 2, "extra_bed": False, "extra_bed_price": 0},
    {"id": 5, "name": "5️⃣ Стандарт 3-местный", "price": 2500, "capacity": 3, "extra_bed": False, "extra_bed_price": 0},
    {"id": 6, "name": "6️⃣ Стандарт 3-местный", "price": 2500, "capacity": 3, "extra_bed": False, "extra_bed_price": 0},
]

# ==============================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

DB_NAME = "hotel.db"


# ================== БАЗА ДАННЫХ ==================
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER,
                guest_name TEXT,
                phone TEXT,
                guest_chat_id INTEGER,
                guests_count INTEGER DEFAULT 1,
                check_in TEXT,
                check_out TEXT,
                price_per_day INTEGER,
                total_days INTEGER,
                total_price INTEGER,
                extra_bed INTEGER DEFAULT 0,
                extra_bed_price INTEGER DEFAULT 0,
                prepay INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS room_photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER,
                photo_file_id TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guest_name TEXT,
                phone TEXT,
                guest_chat_id INTEGER,
                transfer_type TEXT,
                pickup_address TEXT,
                transfer_date TEXT,
                transfer_time TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT
            )
        """)
        await db.commit()


async def add_booking(room_id, guest_name, phone, guest_chat_id, guests_count, check_in, check_out, price_per_day, total_days, total_price, extra_bed=0, extra_bed_price=0):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            INSERT INTO bookings (room_id, guest_name, phone, guest_chat_id, guests_count, check_in, check_out, price_per_day, total_days, total_price, extra_bed, extra_bed_price, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (room_id, guest_name, phone, guest_chat_id, guests_count, check_in, check_out, price_per_day, total_days, total_price, extra_bed, extra_bed_price, datetime.now().isoformat()))
        await db.commit()
        return cursor.lastrowid


async def get_bookings(room_id=None, status=None):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        if room_id and status:
            rows = await db.execute_fetchall(
                "SELECT * FROM bookings WHERE room_id=? AND status=? ORDER BY check_in",
                (room_id, status)
            )
        elif room_id:
            rows = await db.execute_fetchall(
                "SELECT * FROM bookings WHERE room_id=? ORDER BY check_in",
                (room_id,)
            )
        elif status:
            rows = await db.execute_fetchall(
                "SELECT * FROM bookings WHERE status=? ORDER BY check_in",
                (status,)
            )
        else:
            rows = await db.execute_fetchall("SELECT * FROM bookings ORDER BY check_in")
        return [dict(row) for row in rows]


async def update_booking_status(booking_id, status, prepay=None):
    async with aiosqlite.connect(DB_NAME) as db:
        if prepay is not None:
            await db.execute("UPDATE bookings SET status=?, prepay=? WHERE id=?", (status, prepay, booking_id))
        else:
            await db.execute("UPDATE bookings SET status=? WHERE id=?", (status, booking_id))
        await db.commit()


async def get_booking(booking_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        row = await db.execute_fetchall("SELECT * FROM bookings WHERE id=?", (booking_id,))
        return dict(row[0]) if row else None


async def delete_booking(booking_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM bookings WHERE id=?", (booking_id,))
        await db.commit()


async def add_room_photo(room_id, photo_file_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO room_photos (room_id, photo_file_id) VALUES (?, ?)", (room_id, photo_file_id))
        await db.commit()


async def get_room_photos(room_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall("SELECT photo_file_id FROM room_photos WHERE room_id=?", (room_id,))
        return [dict(row) for row in rows]


async def add_transfer(guest_name, phone, guest_chat_id, transfer_type, pickup_address, transfer_date, transfer_time):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            INSERT INTO transfers (guest_name, phone, guest_chat_id, transfer_type, pickup_address, transfer_date, transfer_time, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (guest_name, phone, guest_chat_id, transfer_type, pickup_address, transfer_date, transfer_time, datetime.now().isoformat()))
        await db.commit()
        return cursor.lastrowid


# ================== КЛАВИАТУРЫ ==================
def main_menu():
    kb = ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text="🏨 О нашем доме"), KeyboardButton(text="📅 Свободные номера")],
            [KeyboardButton(text="🛏️ Забронировать"), KeyboardButton(text="📞 Контакты")],
            [KeyboardButton(text="🚕 Трансфер"), KeyboardButton(text="💬 Чат с владельцем")],
            [KeyboardButton(text="🏠 Главное меню")],
        ]
    )
    return kb


def admin_menu():
    kb = ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text="📊 Все бронирования"), KeyboardButton(text="📋 Таблица занятости")],
            [KeyboardButton(text="➕ Добавить бронь"), KeyboardButton(text="🗑️ Удалить бронь")],
            [KeyboardButton(text="💰 Оплаты на проверке"), KeyboardButton(text="🖼️ Добавить фото номера")],
            [KeyboardButton(text="🚕 Заявки на трансфер"), KeyboardButton(text="🏠 Главное меню")]
        ]
    )
    return kb


def back_kb():
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[[KeyboardButton(text="🔙 Назад")], [KeyboardButton(text="🏠 Главное меню")]]
    )


def rooms_kb():
    buttons = []
    for r in ROOMS:
        extra = " +доп" if r.get("extra_bed") else ""
        buttons.append([InlineKeyboardButton(text=f"{r['name']}{extra}", callback_data=f"room_{r['id']}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def rooms_kb_for_admin():
    buttons = []
    for r in ROOMS:
        buttons.append([InlineKeyboardButton(text=r["name"], callback_data=f"adminroom_{r['id']}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def date_nav_kb(year, month, prefix="date"):
    buttons = []
    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    buttons.append([InlineKeyboardButton(text=d, callback_data="noop") for d in days])
    
    import calendar
    cal = calendar.Calendar()
    month_days = cal.monthdayscalendar(year, month)
    
    for week in month_days:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data="noop"))
            else:
                date_str = f"{year}-{month:02d}-{day:02d}"
                row.append(InlineKeyboardButton(text=str(day), callback_data=f"{prefix}_{date_str}"))
        buttons.append(row)
    
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    buttons.append([
        InlineKeyboardButton(text="◀️", callback_data=f"nav_{prefix}_{prev_year}_{prev_month}"),
        InlineKeyboardButton(text=f"{month}.{year}", callback_data="noop"),
        InlineKeyboardButton(text="▶️", callback_data=f"nav_{prefix}_{next_year}_{next_month}")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_confirm_kb(booking_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить оплату", callback_data=f"confirm_pay_{booking_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_pay_{booking_id}")
        ]
    ])


def transfer_type_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚂 Вокзал", callback_data="trans_station")],
        [InlineKeyboardButton(text="✈️ Аэропорт", callback_data="trans_airport")],
    ])


def support_chat_kb():
    if OWNER_USERNAME:
        url = f"https://t.me/{OWNER_USERNAME}"
    else:
        url = f"tg://user?id={ADMIN_IDS[0]}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Написать владельцу", url=url)]
    ])


# ================== СОСТОЯНИЯ FSM ==================
class BookingState(StatesGroup):
    check_in = State()
    check_out = State()
    room = State()
    guests = State()
    extra_bed = State()
    name = State()
    phone = State()
    confirm = State()


class AdminAddState(StatesGroup):
    room = State()
    check_in = State()
    check_out = State()
    name = State()
    phone = State()
    guests = State()
    price = State()


class AdminConfirmPay(StatesGroup):
    booking_id = State()
    prepay = State()


class AdminAddPhoto(StatesGroup):
    room = State()
    photo = State()


class TransferState(StatesGroup):
    type = State()
    address = State()
    date = State()
    time = State()
    name = State()
    phone = State()


# ================== ХЕЛПЕР ДЛЯ НАЗАД ==================
STATE_FLOW = {
    BookingState.phone: BookingState.name,
    BookingState.name: BookingState.guests,
    BookingState.guests: BookingState.room,
    BookingState.room: BookingState.check_out,
    BookingState.check_out: BookingState.check_in,
    BookingState.extra_bed: BookingState.guests,
}

TRANSFER_FLOW = {
    TransferState.phone: TransferState.name,
    TransferState.name: TransferState.time,
    TransferState.time: TransferState.date,
    TransferState.date: TransferState.address,
    TransferState.address: TransferState.type,
}

ADMIN_FLOW = {
    AdminAddState.price: AdminAddState.phone,
    AdminAddState.phone: AdminAddState.name,
    AdminAddState.name: AdminAddState.guests,
    AdminAddState.guests: AdminAddState.check_out,
    AdminAddState.check_out: AdminAddState.check_in,
    AdminAddState.check_in: AdminAddState.room,
}


# ================== ОБРАБОТЧИКИ ==================
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    if message.from_user.id in ADMIN_IDS:
        await message.answer(
            f"👋 Добро пожаловать, {OWNER_NAME}!\n"
            f"Вы вошли как администратор.",
            reply_markup=admin_menu()
        )
    else:
        await message.answer(
            f"👋 Добро пожаловать в {HOTEL_NAME}!\n\n"
            f"Я помогу вам забронировать номер, заказать трансфер и узнать всё о нашем доме.",
            reply_markup=main_menu()
        )


@dp.message(F.text == "🏠 Главное меню")
async def go_main(message: types.Message, state: FSMContext):
    await state.clear()
    if message.from_user.id in ADMIN_IDS:
        await message.answer("Главное меню", reply_markup=admin_menu())
    else:
        await message.answer("Главное меню", reply_markup=main_menu())


@dp.message(F.text == "🔙 Назад")
async def back_button(message: types.Message, state: FSMContext):
    current = await state.get_state()
    if not current:
        await message.answer("Назад некуда — вы в начале.", reply_markup=main_menu())
        return
    
    # Определяем текущее состояние
    current_state = current.split(":")[-1]
    
    # Проверяем бронирование
    for st, prev in STATE_FLOW.items():
        if current_state == st.state:
            await state.set_state(prev)
            if prev == BookingState.check_in:
                now = datetime.now()
                await message.answer("📅 Выберите дату заезда:", reply_markup=date_nav_kb(now.year, now.month, prefix="book"))
            elif prev == BookingState.check_out:
                data = await state.get_data()
                await message.answer(f"📅 Заезд: {data['check_in']}\n\nВыберите дату выезда:", reply_markup=date_nav_kb(datetime.strptime(data['check_in'], "%Y-%m-%d").year, datetime.strptime(data['check_in'], "%Y-%m-%d").month, prefix="book"))
            elif prev == BookingState.room:
                await message.answer("Выберите номер:", reply_markup=rooms_kb())
            elif prev == BookingState.guests:
                await message.answer("Введите количество гостей (число):", reply_markup=back_kb())
            elif prev == BookingState.name:
                await message.answer("👤 Введите ваше ФИО:", reply_markup=back_kb())
            return
    
    # Проверяем трансфер
    for st, prev in TRANSFER_FLOW.items():
        if current_state == st.state:
            await state.set_state(prev)
            if prev == TransferState.type:
                await message.answer("Выберите, откуда вас нужно забрать:", reply_markup=transfer_type_kb())
            elif prev == TransferState.address:
                await message.answer("📍 Введите адрес, где вас забрать (улица, дом, ориентир):", reply_markup=back_kb())
            elif prev == TransferState.date:
                await message.answer("📅 Введите дату трансфера (в формате ДД.ММ.ГГГГ или ГГГГ-ММ-ДД):", reply_markup=back_kb())
            elif prev == TransferState.time:
                await message.answer("🕐 Введите время трансфера (например, 14:30):", reply_markup=back_kb())
            elif prev == TransferState.name:
                await message.answer("👤 Введите ваше ФИО:", reply_markup=back_kb())
            return
    
    # Проверяем админку
    for st, prev in ADMIN_FLOW.items():
        if current_state == st.state:
            await state.set_state(prev)
            if prev == AdminAddState.room:
                await message.answer("Выберите номер:", reply_markup=rooms_kb_for_admin())
            elif prev == AdminAddState.check_in:
                await message.answer("Введите дату заезда (ГГГГ-ММ-ДД или ДД.ММ.ГГГГ):", reply_markup=back_kb())
            elif prev == AdminAddState.check_out:
                await message.answer("Введите дату выезда (ГГГГ-ММ-ДД или ДД.ММ.ГГГГ):", reply_markup=back_kb())
            elif prev == AdminAddState.guests:
                await message.answer("Введите количество гостей:", reply_markup=back_kb())
            elif prev == AdminAddState.name:
                await message.answer("Введите ФИО гостя:", reply_markup=back_kb())
            elif prev == AdminAddState.phone:
                await message.answer("Введите телефон гостя:", reply_markup=back_kb())
            return
    
    await message.answer("Назад некуда.", reply_markup=main_menu())


# ================== О НАШЕМ ДОМЕ ==================
@dp.message(F.text.contains("О нашем доме"))
async def about_hotel(message: types.Message):
    text = (
        f"🏨 <b>{HOTEL_NAME}</b>\n\n"
        f"{DESCRIPTION}\n\n"
        f"👤 Владелец: <b>{OWNER_NAME}</b>\n"
        f"📍 Адрес: <code>{ADDRESS}</code>\n"
        f"📞 Телефон: <code>{PHONE}</code>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗺️ Открыть карту", url=MAP_LINK)],
    ])
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


# ================== КОНТАКТЫ ==================
@dp.message(F.text.contains("Контакты"))
async def contacts(message: types.Message):
    await message.answer(
        f"📞 <b>Контакты</b>\n\n"
        f"Владелец: {OWNER_NAME}\n"
        f"Телефон: <code>{PHONE}</code>\n"
        f"Адрес: {ADDRESS}\n\n"
        f"Напишите нам в Telegram или позвоните по телефону выше.",
        parse_mode="HTML"
    )


# ================== ЧАТ С ВЛАДЕЛЬЦЕМ ==================
@dp.message(F.text.contains("Чат с владельцем"))
async def support_chat(message: types.Message):
    await message.answer(
        f"💬 <b>Связь с владельцем</b>\n\n"
        f"Нажмите кнопку ниже, чтобы перейти в личный чат с {OWNER_NAME}.\n"
        f"Вы можете задать любые вопросы о проживании, трансфере и услугах.",
        reply_markup=support_chat_kb(),
        parse_mode="HTML"
    )


# ================== ТРАНСФЕР ==================
@dp.message(F.text.contains("Заявки на трансфер"))
async def admin_transfer_btn(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    await admin_transfers(message)


@dp.message(F.text.contains("Трансфер"))
async def transfer_start(message: types.Message, state: FSMContext):
    if message.from_user.id in ADMIN_IDS:
        return
    await state.clear()
    await message.answer(
        "🚕 <b>Заказ трансфера</b>\n\n"
        "Выберите, откуда вас нужно забрать:",
        reply_markup=transfer_type_kb()
    )
    await state.set_state(TransferState.type)


@dp.callback_query(TransferState.type, F.data.startswith("trans_"))
async def transfer_type_selected(callback: types.CallbackQuery, state: FSMContext):
    t_type = "вокзала" if callback.data == "trans_station" else "аэропорта"
    await state.update_data(transfer_type=t_type)
    await callback.message.edit_text(
        f"✅ Трансфер с <b>{t_type}</b>.\n\n"
        f"📍 Введите адрес, где вас забрать (улица, дом, ориентир):",
        parse_mode="HTML"
    )
    await state.set_state(TransferState.address)


@dp.message(TransferState.address)
async def transfer_address(message: types.Message, state: FSMContext):
    await state.update_data(pickup_address=message.text)
    await message.answer("📅 Введите дату трансфера (в формате ДД.ММ.ГГГГ или ГГГГ-ММ-ДД):", reply_markup=back_kb())
    await state.set_state(TransferState.date)


@dp.message(TransferState.date)
async def transfer_date(message: types.Message, state: FSMContext):
    await state.update_data(transfer_date=message.text)
    await message.answer("🕐 Введите время трансфера (например, 14:30):", reply_markup=back_kb())
    await state.set_state(TransferState.time)


@dp.message(TransferState.time)
async def transfer_time(message: types.Message, state: FSMContext):
    await state.update_data(transfer_time=message.text)
    await message.answer("👤 Введите ваше ФИО:", reply_markup=back_kb())
    await state.set_state(TransferState.name)


@dp.message(TransferState.name)
async def transfer_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("📱 Введите номер телефона для связи:", reply_markup=back_kb())
    await state.set_state(TransferState.phone)


@dp.message(TransferState.phone)
async def transfer_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    phone = message.text
    guest_chat_id = message.from_user.id
    
    transfer_id = await add_transfer(
        data["name"], phone, guest_chat_id,
        data["transfer_type"], data["pickup_address"],
        data["transfer_date"], data["transfer_time"]
    )
    
    admin_text = (
        f"🚕 <b>Новая заявка на трансфер #{transfer_id}</b>\n\n"
        f"👤 Гость: {data['name']}\n"
        f"📱 Телефон: {phone}\n"
        f"🚗 Тип: с {data['transfer_type']}\n"
        f"📍 Адрес: {data['pickup_address']}\n"
        f"📅 Дата: {data['transfer_date']}\n"
        f"🕐 Время: {data['transfer_time']}\n\n"
        f"Свяжитесь с гостем для подтверждения."
    )
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_text, parse_mode="HTML")
        except Exception:
            pass
    
    await message.answer(
        f"✅ <b>Заявка #{transfer_id} отправлена!</b>\n\n"
        f"🚕 Трансфер с {data['transfer_type']}\n"
        f"📍 {data['pickup_address']}\n"
        f"📅 {data['transfer_date']} в {data['transfer_time']}\n\n"
        f"Владелец свяжется с вами для подтверждения.\n"
        f"Если нужно уточнить детали — нажмите «💬 Чат с владельцем».",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )
    await state.clear()


async def admin_transfers(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall("SELECT * FROM transfers ORDER BY created_at DESC LIMIT 20")
        transfers = [dict(row) for row in rows]
    
    if not transfers:
        await message.answer("📭 Заявок на трансфер пока нет.")
        return
    
    text = "🚕 <b>Заявки на трансфер:</b>\n\n"
    for t in transfers:
        status = {"pending": "⏳", "confirmed": "✅", "cancelled": "❌"}.get(t["status"], "❓")
        text += (
            f"{status} <b>#{t['id']}</b>\n"
            f"   👤 {t['guest_name']} | 📱 {t['phone']}\n"
            f"   🚗 С {t['transfer_type']} | 📍 {t['pickup_address']}\n"
            f"   📅 {t['transfer_date']} {t['transfer_time']}\n\n"
        )
    await message.answer(text, parse_mode="HTML")


# ================== ТАБЛИЦА ЗАНЯТОСТИ ==================
@dp.message(F.text.contains("Таблица занятости"))
async def occupancy_table(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await state.clear()
    await show_occupancy(message, offset=0)


async def show_occupancy(message: types.Message, offset: int):
    start_date = date.today() + timedelta(days=offset)
    dates = [start_date + timedelta(days=i) for i in range(7)]
    
    bookings = await get_bookings()
    occupied = {}
    for b in bookings:
        if b["status"] == "cancelled":
            continue
        b_in = datetime.strptime(b["check_in"], "%Y-%m-%d").date()
        b_out = datetime.strptime(b["check_out"], "%Y-%m-%d").date()
        for d in dates:
            if b_in <= d < b_out:
                occupied.setdefault(b["room_id"], set()).add(d)
    
    text = f"📋 <b>Занятость с {dates[0].strftime('%d.%m')} по {dates[-1].strftime('%d.%m')}</b>\n\n"
    text += "<code>Номер   | " + " | ".join([d.strftime("%d.%m") for d in dates]) + "</code>\n"
    text += "<code>" + "-" * 50 + "</code>\n"
    
    for r in ROOMS:
        row = f"<code>{r['name'][:7]:7} |</code> "
        cells = []
        for d in dates:
            if d in occupied.get(r["id"], set()):
                cells.append("🔴")
            else:
                cells.append("🟢")
        row += " | ".join(cells)
        text += row + "\n"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data=f"occ_{offset-7}"),
            InlineKeyboardButton(text="▶️ Вперед", callback_data=f"occ_{offset+7}")
        ]
    ])
    
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@dp.callback_query(F.data.startswith("occ_"))
async def occupancy_nav(callback: types.CallbackQuery, state: FSMContext):
    offset = int(callback.data.split("_")[1])
    await callback.message.delete()
    await show_occupancy(callback.message, offset)
    await callback.answer()


# ================== БРОНИРОВАНИЕ ==================
@dp.message(F.text.contains("Свободные номера"))
async def free_rooms_start(message: types.Message, state: FSMContext):
    await state.clear()
    now = datetime.now()
    await message.answer(
        "📅 Выберите дату заезда:",
        reply_markup=date_nav_kb(now.year, now.month, prefix="free")
    )


@dp.callback_query(F.data.startswith("nav_free_"))
async def navigate_free_calendar(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    year, month = int(parts[2]), int(parts[3])
    await callback.message.edit_reply_markup(
        reply_markup=date_nav_kb(year, month, prefix="free")
    )


@dp.callback_query(F.data.startswith("free_"))
async def select_free_date(callback: types.CallbackQuery, state: FSMContext):
    date_str = callback.data.replace("free_", "")
    data = await state.get_data()
    
    if "check_in" not in data:
        await state.update_data(check_in=date_str)
        await callback.message.edit_text(
            f"📅 Заезд: <b>{date_str}</b>\n\nВыберите дату выезда:",
            reply_markup=date_nav_kb(
                datetime.strptime(date_str, "%Y-%m-%d").year,
                datetime.strptime(date_str, "%Y-%m-%d").month,
                prefix="free"
            ),
            parse_mode="HTML"
        )
    else:
        check_in = data["check_in"]
        check_out = date_str
        
        if check_out <= check_in:
            await callback.answer("❌ Дата выезда должна быть позже заезда!", show_alert=True)
            return
        
        await state.clear()
        free = await get_free_rooms(check_in, check_out)
        
        if not free:
            await callback.message.edit_text(
                "😔 На эти даты нет свободных номеров.\nПопробуйте другие даты.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Выбрать даты", callback_data="restart_free")]
                ])
            )
            return
        
        text = f"📅 <b>{check_in}</b> → <b>{check_out}</b>\n\nСвободные номера:"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{r['name']} — {r['price']}₽/сут (до {r['capacity']} чел)", callback_data=f"freeroom_{r['id']}_{check_in}_{check_out}")]
            for r in free
        ])
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")


@dp.callback_query(F.data == "restart_free")
async def restart_free(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    now = datetime.now()
    await callback.message.edit_text("📅 Выберите дату заезда:", reply_markup=date_nav_kb(now.year, now.month, prefix="free"))


@dp.callback_query(F.data.startswith("freeroom_"))
async def free_room_info(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    room_id = int(parts[1])
    check_in = parts[2]
    check_out = parts[3]
    room = next(r for r in ROOMS if r["id"] == room_id)
    
    photos = await get_room_photos(room_id)
    
    c_in = datetime.strptime(check_in, "%Y-%m-%d").date()
    c_out = datetime.strptime(check_out, "%Y-%m-%d").date()
    days = (c_out - c_in).days
    total = days * room["price"]
    
    extra_info = ""
    if room.get("extra_bed"):
        extra_info = f"\n🛏️ Можно добавить доп кровать (бесплатно)"
    
    text = (
        f"🛏️ <b>{room['name']}</b>\n"
        f"👥 Вместимость: до <b>{room['capacity']}</b> гостей{extra_info}\n"
        f"💰 <b>{room['price']}₽</b> за сутки\n"
        f"📅 {check_in} → {check_out} ({days} суток)\n"
        f"💰 Итого: <b>{total}₽</b>\n\n"
        f"Для бронирования нажмите кнопку ниже."
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Забронировать", callback_data=f"bookstart_{room_id}_{check_in}_{check_out}")]
    ])
    
    if photos:
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=photos[0]["photo_file_id"],
            caption=text,
            reply_markup=kb,
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    
    await callback.answer()


@dp.callback_query(F.data.startswith("bookstart_"))
async def bookstart_from_free(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    room_id = int(parts[1])
    check_in = parts[2]
    check_out = parts[3]
    room = next(r for r in ROOMS if r["id"] == room_id)
    
    await state.update_data(room_id=room_id, price=room["price"], check_in=check_in, check_out=check_out)
    await state.set_state(BookingState.guests)
    
    extra_hint = ""
    if room.get("extra_bed"):
        extra_hint = f"\n🛏️ Доп кровать доступна (бесплатно)"
    
    await callback.message.delete()
    await callback.message.answer(
        f"✅ Выбран: <b>{room['name']}</b>\n"
        f"👥 Вместимость: до {room['capacity']} гостей{extra_hint}\n"
        f"💰 Цена: <b>{room['price']}₽</b> за сутки\n"
        f"📅 {check_in} → {check_out}\n\n"
        f"Введите количество гостей (число):",
        reply_markup=back_kb(),
        parse_mode="HTML"
    )


@dp.message(F.text.contains("Забронировать"))
async def book_start(message: types.Message, state: FSMContext):
    if message.from_user.id in ADMIN_IDS:
        return
    await state.clear()
    now = datetime.now()
    await state.set_state(BookingState.check_in)
    await message.answer(
        "📅 Выберите дату заезда:",
        reply_markup=date_nav_kb(now.year, now.month, prefix="book")
    )


@dp.callback_query(F.data.startswith("nav_book_"))
async def navigate_book_calendar(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    year, month = int(parts[2]), int(parts[3])
    await callback.message.edit_reply_markup(
        reply_markup=date_nav_kb(year, month, prefix="book")
    )


@dp.callback_query(F.data.startswith("book_"))
async def select_book_date(callback: types.CallbackQuery, state: FSMContext):
    date_str = callback.data.replace("book_", "")
    current = await state.get_state()
    
    if current == BookingState.check_in:
        await state.update_data(check_in=date_str)
        await state.set_state(BookingState.check_out)
        await callback.message.edit_text(
            f"📅 Заезд: <b>{date_str}</b>\n\nВыберите дату выезда:",
            reply_markup=date_nav_kb(
                datetime.strptime(date_str, "%Y-%m-%d").year,
                datetime.strptime(date_str, "%Y-%m-%d").month,
                prefix="book"
            ),
            parse_mode="HTML"
        )
    elif current == BookingState.check_out:
        data = await state.get_data()
        check_in = data["check_in"]
        check_out = date_str
        
        if check_out <= check_in:
            await callback.answer("❌ Дата выезда должна быть позже заезда!", show_alert=True)
            return
        
        await state.update_data(check_out=check_out)
        free = await get_free_rooms(check_in, check_out)
        
        if not free:
            await callback.message.edit_text(
                "😔 На эти даты нет свободных номеров.\nПопробуйте другие даты.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Выбрать даты", callback_data="restart_book")]
                ])
            )
            await state.clear()
            return
        
        text = f"📅 <b>{check_in}</b> → <b>{check_out}</b>\n\nВыберите номер:"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{r['name']} — {r['price']}₽/сут (до {r['capacity']} чел)", callback_data=f"bookroom_{r['id']}")]
            for r in free
        ])
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        await state.set_state(BookingState.room)


@dp.callback_query(F.data == "restart_book")
async def restart_book(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(BookingState.check_in)
    now = datetime.now()
    await callback.message.edit_text("📅 Выберите дату заезда:", reply_markup=date_nav_kb(now.year, now.month, prefix="book"))


async def get_free_rooms(check_in, check_out):
    all_rooms = {r["id"]: r for r in ROOMS}
    bookings = await get_bookings()
    
    occupied = set()
    for b in bookings:
        if b["status"] == "cancelled":
            continue
        b_in = datetime.strptime(b["check_in"], "%Y-%m-%d").date()
        b_out = datetime.strptime(b["check_out"], "%Y-%m-%d").date()
        c_in = datetime.strptime(check_in, "%Y-%m-%d").date()
        c_out = datetime.strptime(check_out, "%Y-%m-%d").date()
        
        if not (c_out <= b_in or c_in >= b_out):
            occupied.add(b["room_id"])
    
    return [all_rooms[r] for r in all_rooms if r not in occupied]


@dp.callback_query(F.data.startswith("bookroom_"))
async def select_room(callback: types.CallbackQuery, state: FSMContext):
    room_id = int(callback.data.split("_")[1])
    room = next(r for r in ROOMS if r["id"] == room_id)
    await state.update_data(room_id=room_id, price=room["price"])
    
    photos = await get_room_photos(room_id)
    
    extra_hint = ""
    if room.get("extra_bed"):
        extra_hint = f"\n🛏️ Доп кровать доступна (бесплатно)"
    
    text = (
        f"✅ Выбран: <b>{room['name']}</b>\n"
        f"👥 Вместимость: до {room['capacity']} гостей{extra_hint}\n"
        f"💰 Цена: <b>{room['price']}₽</b> за сутки\n\n"
        f"Введите количество гостей (число):"
    )
    
    if photos:
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=photos[0]["photo_file_id"],
            caption=text,
            reply_markup=back_kb(),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(text, reply_markup=back_kb(), parse_mode="HTML")
    
    await state.set_state(BookingState.guests)


@dp.message(BookingState.guests)
async def get_guests_count(message: types.Message, state: FSMContext):
    try:
        guests = int(message.text)
    except ValueError:
        await message.answer("❌ Введите число.")
        return
    
    if guests < 1:
        await message.answer("❌ Количество гостей должно быть хотя бы 1.")
        return
    
    data = await state.get_data()
    room_id = data["room_id"]
    room = next(r for r in ROOMS if r["id"] == room_id)
    
    max_with_extra = room["capacity"] + (1 if room.get("extra_bed") else 0)
    
    if guests > max_with_extra:
        text = (
            f"❌ Номер <b>{room['name']}</b> рассчитан максимум на <b>{room['capacity']}</b> гостей"
        )
        if room.get("extra_bed"):
            text += f" (+1 доп кровать, итого {max_with_extra})"
        text += f".\n\nВы указали <b>{guests}</b> гостей.\n"
        
        if guests >= 4:
            text += (
                "💡 <b>Рекомендация:</b> забронируйте несколько номеров, "
                "чтобы вся компания была у вас.\n"
                "Например, номер на 3 человека + номер на 2 человека."
            )
        else:
            text += "💡 Выберите другой номер с большей вместимостью."
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 К выбору номеров", callback_data="restart_book")]
        ])
        await message.answer(text, reply_markup=kb, parse_mode="HTML")
        return
    
    if guests > room["capacity"] and room.get("extra_bed"):
        await state.update_data(guests_count=guests)
        text = (
            f"🛏️ Номер <b>{room['name']}</b> рассчитан на <b>{room['capacity']}</b> гостей.\n"
            f"Вы указали <b>{guests}</b> гостей.\n\n"
            f"Выберите вариант:"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Добавить доп кровать (бесплатно)", callback_data="extra_bed_yes")],
            [InlineKeyboardButton(text="🛏️ Забронировать ещё один номер", callback_data="book_another_room")],
            [InlineKeyboardButton(text="👥 Продолжить без доп кровати", callback_data="extra_bed_no")]
        ])
        await message.answer(text, reply_markup=kb, parse_mode="HTML")
        await state.set_state(BookingState.extra_bed)
        return
    
    await state.update_data(guests_count=guests, extra_bed=0, extra_bed_price=0)
    await message.answer("👤 Введите ваше ФИО:", reply_markup=back_kb())
    await state.set_state(BookingState.name)


@dp.callback_query(F.data == "extra_bed_yes")
async def extra_bed_yes(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    room = next(r for r in ROOMS if r["id"] == data["room_id"])
    await state.update_data(extra_bed=1, extra_bed_price=0)
    await callback.message.edit_text(
        f"✅ Дополнительная кровать добавлена (бесплатно).\n\n"
        f"Введите ваше ФИО:"
    )
    await state.set_state(BookingState.name)


@dp.callback_query(F.data == "book_another_room")
async def book_another_room(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_room = next(r for r in ROOMS if r["id"] == data["room_id"])
    
    await callback.message.edit_text(
        f"🛏️ Вы решили забронировать ещё один номер.\n"
        f"Сейчас вы бронируете: <b>{current_room['name']}</b> "
        f"на {data['guests_count']} гостей.\n\n"
        f"Давайте выберем дополнительный номер для оставшихся гостей.\n\n"
        f"📅 Заезд: {data['check_in']}\n"
        f"📅 Выезд: {data['check_out']}\n\n"
        f"Выберите номер из списка:"
    )
    
    free = await get_free_rooms(data["check_in"], data["check_out"])
    free = [r for r in free if r["id"] != current_room["id"]]
    
    if not free:
        await callback.message.edit_text(
            "😔 К сожалению, на эти даты нет других свободных номеров.\n\n"
            "💡 Рекомендуем:\n"
            "• Выбрать другие даты\n"
            "• Или воспользоваться доп кроватью\n\n"
            "Нажмите «🛏️ Забронировать» для нового поиска.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 К выбору номеров", callback_data="restart_book")]
            ])
        )
        return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{r['name']} — {r['price']}₽/сут (до {r['capacity']} чел)", callback_data=f"bookroom_{r['id']}")]
        for r in free
    ])
    await callback.message.edit_reply_markup(reply_markup=kb)
    await state.set_state(BookingState.room)
    await callback.answer()


@dp.callback_query(F.data == "extra_bed_no")
async def extra_bed_no(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    room = next(r for r in ROOMS if r["id"] == data["room_id"])
    
    await state.update_data(extra_bed=0, extra_bed_price=0)
    await callback.message.edit_text(
        f"⚠️ <b>Внимание!</b> Вы выбрали продолжить без доп кровати.\n"
        f"Номер <b>{room['name']}</b> рассчитан на <b>{room['capacity']}</b> гостей, "
        f"а вы указали <b>{data['guests_count']}</b>.\n\n"
        f"Гости будут потеснее, но бронь возможна.\n\n"
        f"Введите ваше ФИО:"
    )
    await state.set_state(BookingState.name)
    await callback.answer()


@dp.message(BookingState.name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("📱 Введите номер телефона для связи:", reply_markup=back_kb())
    await state.set_state(BookingState.phone)


@dp.message(BookingState.phone)
async def get_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text, guest_chat_id=message.from_user.id)
    data = await state.get_data()
    
    c_in = datetime.strptime(data["check_in"], "%Y-%m-%d").date()
    c_out = datetime.strptime(data["check_out"], "%Y-%m-%d").date()
    days = (c_out - c_in).days
    room = next(r for r in ROOMS if r["id"] == data["room_id"])
    
    extra_bed_price = data.get("extra_bed_price", 0)
    room_total = days * data["price"]
    extra_total = days * extra_bed_price
    total = room_total + extra_total
    
    prepay_10 = int(total * 0.1)
    
    text = (
        f"📝 <b>Проверьте данные бронирования:</b>\n\n"
        f"🛏️ Номер: {room['name']}\n"
        f"👥 Гостей: {data['guests_count']}\n"
    )
    if extra_bed_price > 0:
        text += f"🛏️ Доп кровать: {extra_bed_price}₽ × {days} сут = {extra_total}₽\n"
    elif data.get("extra_bed"):
        text += f"🛏️ Доп кровать: включена (бесплатно)\n"
    text += (
        f"📅 Заезд: {data['check_in']}\n"
        f"📅 Выезд: {data['check_out']}\n"
        f"👤 Гость: {data['name']}\n"
        f"📱 Телефон: {data['phone']}\n"
        f"💰 Суток: {days}\n"
        f"💰 Цена номера: {data['price']}₽/сут\n"
        f"💰 <b>Итого: {total}₽</b>\n\n"
        f"💰 <b>Предоплата 10%: {prepay_10}₽</b>\n\n"
        f"Нажмите ✅ для подтверждения. Вам будут отправлены реквизиты для оплаты."
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Всё верно", callback_data="confirm_book")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_book")]
    ])
    
    await state.update_data(total=total, days=days, prepay_10=prepay_10)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")
    await state.set_state(BookingState.confirm)


@dp.callback_query(F.data == "cancel_book")
async def cancel_book(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Бронирование отменено.")
    await callback.message.answer("Главное меню", reply_markup=main_menu())


@dp.callback_query(F.data == "confirm_book")
async def confirm_book(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    booking_id = await add_booking(
        data["room_id"], data["name"], data["phone"], data["guest_chat_id"],
        data["guests_count"], data["check_in"], data["check_out"],
        data["price"], data["days"], data["total"],
        data.get("extra_bed", 0), data.get("extra_bed_price", 0)
    )
    
    room = next(r for r in ROOMS if r["id"] == data["room_id"])
    prepay_10 = data["prepay_10"]
    
    admin_text = (
        f"🔔 <b>Новая бронь #{booking_id}</b>\n\n"
        f"🛏️ Номер: {room['name']}\n"
        f"👥 Гостей: {data['guests_count']}\n"
    )
    if data.get("extra_bed"):
        admin_text += f"🛏️ Доп кровать: включена\n"
    admin_text += (
        f"👤 Гость: {data['name']}\n"
        f"📱 Телефон: {data['phone']}\n"
        f"📅 Заезд: {data['check_in']}\n"
        f"📅 Выезд: {data['check_out']}\n"
        f"💰 Суток: {data['days']}\n"
        f"💰 Цена/сутки: {data['price']}₽\n"
        f"💰 Итого: {data['total']}₽\n"
        f"💰 Предоплата 10%: {prepay_10}₽\n"
        f"⏳ Статус: ожидает оплату\n\n"
        f"Гость должен отправить чек в этот чат."
    )
    
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_text, parse_mode="HTML")
        except Exception:
            pass
    
    guest_text = (
        f"✅ <b>Бронь #{booking_id} создана!</b>\n\n"
        f"🛏️ {room['name']}\n"
        f"👥 Гостей: {data['guests_count']}\n"
    )
    if data.get("extra_bed"):
        guest_text += f"🛏️ Доп кровать включена (бесплатно)\n"
    guest_text += (
        f"📅 {data['check_in']} → {data['check_out']}\n"
        f"💰 К оплате: <b>{data['total']}₽</b>\n"
        f"💰 Предоплата (10%): <b>{prepay_10}₽</b>\n\n"
        f"Для подтверждения отправьте скриншот чека об оплате "
        f"в этот чат. После проверки владельцем дома вы получите "
        f"подтверждение.\n\n"
        f"🏦 Реквизиты для оплаты:\n"
        f"Сбербанк: {PHONE}\n"
        f"Получатель: {OWNER_NAME}\n"
        f"💰 Сумма предоплаты: {prepay_10}₽"
    )
    
    await state.update_data(booking_id=booking_id)
    await callback.message.edit_text(guest_text, parse_mode="HTML")
    await state.set_state(BookingState.confirm)


# ================== ОПЛАТА ==================
@dp.message(F.photo, BookingState.confirm)
async def receive_payment_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    booking_id = data.get("booking_id")
    
    if not booking_id:
        await message.answer("❌ Ошибка. Начните бронирование заново: /start")
        return
    
    photo = message.photo[-1].file_id
    booking = await get_booking(booking_id)
    room = next(r for r in ROOMS if r["id"] == booking["room_id"])
    
    admin_text = (
        f"💰 <b>Чек оплаты по брони #{booking_id}</b>\n\n"
        f"🛏️ Номер: {room['name']}\n"
        f"👥 Гостей: {booking['guests_count']}\n"
    )
    if booking.get("extra_bed"):
        admin_text += f"🛏️ Доп кровать: включена\n"
    admin_text += (
        f"👤 Гость: {booking['guest_name']}\n"
        f"📱 Телефон: {booking['phone']}\n"
        f"📅 Заезд: {booking['check_in']}\n"
        f"📅 Выезд: {booking['check_out']}\n"
        f"💰 Общая сумма: {booking['total_price']}₽\n"
        f"💰 Предоплата 10%: {int(booking['total_price'] * 0.1)}₽\n\n"
        f"⚠️ Проверьте перевод и подтвердите бронь."
    )
    
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_photo(
                admin_id,
                photo=photo,
                caption=admin_text,
                reply_markup=admin_confirm_kb(booking_id),
                parse_mode="HTML"
            )
        except Exception:
            pass
    
    await message.answer(
        "📎 Чек получен! Ожидайте подтверждения от владельца дома.\n"
        "Обычно это занимает 10-15 минут."
    )


@dp.callback_query(F.data.startswith("confirm_pay_"))
async def admin_confirm_payment(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    booking_id = int(callback.data.split("_")[2])
    await state.update_data(booking_id=booking_id)
    await state.set_state(AdminConfirmPay.prepay)
    
    await callback.message.answer(
        f"💰 Введите сумму предоплаты по брони #{booking_id} (число):"
    )
    await callback.answer()


@dp.message(AdminConfirmPay.prepay)
async def admin_enter_prepay(message: types.Message, state: FSMContext):
    data = await state.get_data()
    booking_id = data["booking_id"]
    
    try:
        prepay = int(message.text)
    except ValueError:
        await message.answer("❌ Введите число.")
        return
    
    booking = await get_booking(booking_id)
    if not booking:
        await message.answer("❌ Бронь не найдена.")
        await state.clear()
        return
    
    await update_booking_status(booking_id, "confirmed", prepay)
    room = next(r for r in ROOMS if r["id"] == booking["room_id"])
    
    guest_text = (
        f"✅ <b>Бронь подтверждена!</b>\n\n"
        f"🏨 {HOTEL_NAME}\n"
        f"👤 Владелец: {OWNER_NAME}\n\n"
        f"🛏️ У вас забронирован: <b>{room['name']} (№{room['id']})</b>\n"
        f"👥 Гостей: {booking['guests_count']}\n"
    )
    if booking.get("extra_bed"):
        guest_text += f"🛏️ Доп кровать включена (бесплатно)\n"
    guest_text += (
        f"📅 Дата заезда: {booking['check_in']}\n"
        f"📅 Дата выезда: {booking['check_out']}\n"
        f"💰 Сумма предоплаты: {prepay}₽\n"
        f"💰 Общая сумма проживания: {booking['total_price']}₽\n\n"
        f"Ждём вас! По всем вопросам звоните: {PHONE}"
    )
    
    try:
        await bot.send_message(booking["guest_chat_id"], guest_text, parse_mode="HTML")
    except Exception as e:
        await message.answer(f"⚠️ Не удалось отправить сообщение гостю: {e}")
    
    await message.answer(
        f"✅ Бронь #{booking_id} подтверждена!\n"
        f"💰 Предоплата: {prepay}₽\n"
        f"📨 Подтверждение отправлено гостю.",
        reply_markup=admin_menu()
    )
    await state.clear()


@dp.callback_query(F.data.startswith("reject_pay_"))
async def admin_reject_payment(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    booking_id = int(callback.data.split("_")[2])
    booking = await get_booking(booking_id)
    
    await update_booking_status(booking_id, "cancelled")
    
    if booking and booking["guest_chat_id"]:
        try:
            await bot.send_message(
                booking["guest_chat_id"],
                f"❌ <b>Бронь #{booking_id} отклонена</b>\n\n"
                f"Владелец не подтвердил оплату. Свяжитесь по телефону: {PHONE}",
                parse_mode="HTML"
            )
        except Exception:
            pass
    
    await callback.message.edit_caption(
        caption=f"❌ <b>Бронь #{booking_id} ОТКЛОНЕНА</b>",
        parse_mode="HTML"
    )
    await callback.answer("❌ Бронь отклонена")


# ================== АДМИНКА ==================
@dp.message(F.text.contains("Все бронирования"))
async def admin_all_bookings(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    bookings = await get_bookings()
    if not bookings:
        await message.answer("📭 Бронирований пока нет.")
        return
    
    text = "📊 <b>Все бронирования:</b>\n\n"
    for b in bookings:
        room = next(r for r in ROOMS if r["id"] == b["room_id"])
        status = {"pending": "⏳", "confirmed": "✅", "cancelled": "❌"}.get(b["status"], "❓")
        extra = ""
        if b.get("extra_bed"):
            extra = " +доп"
        guests = b.get("guests_count", "?")
        text += (
            f"{status} <b>#{b['id']}</b> | {room['name']}{extra}\n"
            f"   👥 {guests} чел | 👤 {b['guest_name']} | 📱 {b['phone']}\n"
            f"   📅 {b['check_in']} → {b['check_out']}\n"
            f"   💰 {b['total_price']}₽ | Предоплата: {b['prepay']}₽ | {b['status'].upper()}\n\n"
        )
    
    await message.answer(text, parse_mode="HTML")


@dp.message(F.text.contains("Оплаты на проверке"))
async def admin_pending_payments(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    bookings = await get_bookings(status="pending")
    if not bookings:
        await message.answer("📭 Нет броней в ожидании оплаты.")
        return
    
    text = "⏳ <b>Брони в ожидании оплаты:</b>\n\n"
    for b in bookings:
        room = next(r for r in ROOMS if r["id"] == b["room_id"])
        extra = ""
        if b.get("extra_bed"):
            extra = " +доп"
        guests = b.get("guests_count", "?")
        text += (
            f"#{b['id']} | {room['name']}{extra}\n"
            f"👥 {guests} чел | 👤 {b['guest_name']} | 📱 {b['phone']}\n"
            f"📅 {b['check_in']} → {b['check_out']}\n"
            f"💰 {b['total_price']}₽\n\n"
        )
    
    await message.answer(text, parse_mode="HTML")


@dp.message(F.text.contains("Добавить бронь"))
async def admin_add_start(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("Выберите номер:", reply_markup=rooms_kb_for_admin())
    await state.set_state(AdminAddState.room)


@dp.callback_query(AdminAddState.room, F.data.startswith("adminroom_"))
async def admin_add_room(callback: types.CallbackQuery, state: FSMContext):
    room_id = int(callback.data.split("_")[1])
    room = next(r for r in ROOMS if r["id"] == room_id)
    await state.update_data(room_id=room_id, price=room["price"])
    await callback.message.edit_text(
        f"Выбран: {room['name']} ({room['price']}₽/сут, до {room['capacity']} чел)\n\nВведите дату заезда (ГГГГ-ММ-ДД или ДД.ММ.ГГГГ):"
    )
    await state.set_state(AdminAddState.check_in)


def parse_date(date_str):
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d.%m.%y"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Неизвестный формат даты: {date_str}")


@dp.message(AdminAddState.check_in)
async def admin_add_check_in(message: types.Message, state: FSMContext):
    await state.update_data(check_in=message.text)
    await message.answer("Введите дату выезда (ГГГГ-ММ-ДД или ДД.ММ.ГГГГ):", reply_markup=back_kb())
    await state.set_state(AdminAddState.check_out)


@dp.message(AdminAddState.check_out)
async def admin_add_check_out(message: types.Message, state: FSMContext):
    await state.update_data(check_out=message.text)
    await message.answer("Введите количество гостей:", reply_markup=back_kb())
    await state.set_state(AdminAddState.guests)


@dp.message(AdminAddState.guests)
async def admin_add_guests(message: types.Message, state: FSMContext):
    try:
        guests = int(message.text)
    except ValueError:
        await message.answer("❌ Введите число.")
        return
    
    data = await state.get_data()
    room = next(r for r in ROOMS if r["id"] == data["room_id"])
    if guests > room["capacity"] and not room.get("extra_bed"):
        await message.answer(f"❌ Номер рассчитан максимум на {room['capacity']} гостей.")
        return
    if guests > room["capacity"] + 1:
        await message.answer(f"❌ Номер рассчитан максимум на {room['capacity']}+1 гостей.")
        return
    
    await state.update_data(guests_count=guests)
    await message.answer("Введите ФИО гостя:", reply_markup=back_kb())
    await state.set_state(AdminAddState.name)


@dp.message(AdminAddState.name)
async def admin_add_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите телефон гостя:", reply_markup=back_kb())
    await state.set_state(AdminAddState.phone)


@dp.message(AdminAddState.phone)
async def admin_add_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("Введите цену за сутки (число):", reply_markup=back_kb())
    await state.set_state(AdminAddState.price)


@dp.message(AdminAddState.price)
async def admin_add_price(message: types.Message, state: FSMContext):
    data = await state.get_data()
    try:
        price = int(message.text)
    except ValueError:
        await message.answer("❌ Введите число.")
        return
    
    try:
        days = (parse_date(data["check_out"]) - parse_date(data["check_in"])).days
    except ValueError as e:
        await message.answer(f"❌ Ошибка в датах: {e}")
        return
    
    if days <= 0:
        await message.answer("❌ Дата выезда должна быть позже заезда.")
        return
    
    total = days * price
    
    await add_booking(
        data["room_id"], data["name"], data["phone"], None,
        data.get("guests_count", 1), data["check_in"], data["check_out"], price, days, total
    )
    await state.clear()
    await message.answer(f"✅ Бронь добавлена! Итого: {total}₽", reply_markup=admin_menu())


@dp.message(F.text.contains("Удалить бронь"))
async def admin_delete_start(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    bookings = await get_bookings()
    if not bookings:
        await message.answer("📭 Нет броней для удаления.")
        return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"#{b['id']} | {b['guest_name']} | {b['check_in']}",
            callback_data=f"del_{b['id']}"
        )]
        for b in bookings
    ])
    await message.answer("Выберите бронь для удаления:", reply_markup=kb)


@dp.callback_query(F.data.startswith("del_"))
async def admin_delete_confirm(callback: types.CallbackQuery):
    booking_id = int(callback.data.split("_")[1])
    await delete_booking(booking_id)
    await callback.message.edit_text(f"✅ Бронь #{booking_id} удалена.")
    await callback.answer("Удалено")


# ================== ФОТО НОМЕРОВ ==================
@dp.message(Command("addphoto"))
async def cmd_addphoto(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("Выберите номер для загрузки фото:", reply_markup=rooms_kb_for_admin())
    await state.set_state(AdminAddPhoto.room)


@dp.callback_query(AdminAddPhoto.room, F.data.startswith("adminroom_"))
async def admin_select_room_photo(callback: types.CallbackQuery, state: FSMContext):
    room_id = int(callback.data.split("_")[1])
    room = next(r for r in ROOMS if r["id"] == room_id)
    await state.update_data(room_id=room_id)
    await callback.message.edit_text(
        f"📸 Отправьте фото для номера <b>{room['name']}</b>.\n"
        f"Можно отправить несколько фото подряд. Нажмите /done когда закончите.",
        parse_mode="HTML"
    )
    await state.set_state(AdminAddPhoto.photo)


@dp.message(AdminAddPhoto.photo, F.photo)
async def admin_receive_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    room_id = data["room_id"]
    photo_file_id = message.photo[-1].file_id
    await add_room_photo(room_id, photo_file_id)
    await message.answer("✅ Фото сохранено. Отправ Вот продолжение кода (он обрезался в конце")


    await message.answer("✅ Фото сохранено. Отправьте ещё или /done")


@dp.message(AdminAddPhoto.photo, Command("done"))
async def admin_photo_done(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Готово! Фото добавлены.", reply_markup=admin_menu())


@dp.message(F.text.contains("Добавить фото номера"))
async def admin_add_photo_btn(message: types.Message, state: FSMContext):
    await cmd_addphoto(message, state)


# ================== ЗАПУСК ==================
async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
