from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from datetime import datetime, timedelta

from bot.database.methods.slots import get_available_slots, book_slot, get_slot_by_id, get_user_bookings, check_user_booking_limit, cancel_booking
from bot.keyboards.inline.consultation import create_slots_keyboard, create_confirm_keyboard, create_bookings_keyboard, create_booking_details_keyboard
from bot.database.methods.users import get_user_by_chat_id
from bot.misc.env import settings

consultation_router = Router()

@consultation_router.message(Command("schedule"))
async def show_schedule(message: Message):
    from_date = datetime.now()
    to_date = from_date + timedelta(days=14)
    
    available_slots = get_available_slots(from_date, to_date)
    if not available_slots:
        await message.answer("К сожалению, нет доступных слотов для записи.")
        return
    
    keyboard = await create_slots_keyboard(available_slots, page=1)
    await message.answer("Выберите удобное время для консультации:", reply_markup=keyboard)

@consultation_router.callback_query(F.data.startswith("book_"))
async def process_booking(callback: CallbackQuery):
    slot_id = int(callback.data.split("_")[1])
    keyboard = await create_confirm_keyboard(slot_id)
    await callback.message.edit_text(
        "Подтвердите запись на консультацию:",
        reply_markup=keyboard
    )

@consultation_router.callback_query(F.data.startswith("confirm_"))
async def confirm_booking(callback: CallbackQuery):
    slot_id = int(callback.data.split("_")[1])
    user = get_user_by_chat_id(callback.from_user.id)
    
    if not user:
        await callback.message.edit_text("❌ Произошла ошибка. Попробуйте начать сначала с /start")
        return
    
    if not check_user_booking_limit(user.id):
        await callback.message.edit_text(
            f"❌ Превышен лимит бронирований. Максимально доступно: {settings.BOOKING_LIMIT} активных записей."
        )
        return
        
    if book_slot(slot_id, user.id):
        slot = get_slot_by_id(slot_id)
        time_until = slot.datetime - datetime.now()
        
        await callback.message.edit_text("✅ Вы успешно записались на консультацию!")
        
        if time_until <= timedelta(hours=1):
            minutes_left = int(time_until.total_seconds() / 60)
            await callback.message.answer(
                f"⚡️ Ваша консультация начнется через {minutes_left} минут, "
                f"в {slot.datetime.strftime('%H:%M')}!"
            )
    else:
        await callback.message.edit_text("❌ Извините, этот слот уже занят.") 

@consultation_router.message(Command("my_bookings"))
async def show_my_bookings(message: Message):
    user = get_user_by_chat_id(message.from_user.id)
    if not user:
        await message.answer("❌ Произошла ошибка. Попробуйте начать сначала с /start")
        return
        
    bookings = get_user_bookings(user.id)
    active_bookings = len(bookings)
    
    if not bookings:
        await message.answer(
            f"У вас нет предстоящих консультаций.\n"
            f"Доступно записей: {settings.BOOKING_LIMIT}"
        )
        return
    
    keyboard = await create_bookings_keyboard(bookings, page=1)
    await message.answer(
        f"📅 Ваши предстоящие консультации ({active_bookings}/{settings.BOOKING_LIMIT}):",
        reply_markup=keyboard
    )

@consultation_router.callback_query(F.data.startswith("booking_details_"))
async def show_booking_details(callback: CallbackQuery):
    booking_id = int(callback.data.split("_")[2])
    slot = get_slot_by_id(booking_id)
    
    if not slot:
        await callback.answer("Консультация не найдена")
        return
        
    time_until = slot.datetime - datetime.now()
    hours_left = int(time_until.total_seconds() / 3600)
    
    if hours_left < 1:
        time_info = f"через {int(time_until.total_seconds() / 60)} минут"
    else:
        time_info = f"через {hours_left} часов"
    
    keyboard = await create_booking_details_keyboard(booking_id)
    await callback.message.edit_text(
        f"📅 Консультация {slot.datetime.strftime('%d.%m.%Y %H:%M')}\n"
        f"⏳ Начнется {time_info}\n\n"
        "Выберите действие:",
        reply_markup=keyboard
    )

@consultation_router.callback_query(F.data.startswith("cancel_booking_"))
async def process_booking_cancellation(callback: CallbackQuery):
    booking_id = int(callback.data.split("_")[2])
    user = get_user_by_chat_id(callback.from_user.id)
    
    if await cancel_booking(booking_id):
        bookings = get_user_bookings(user.id)
        if bookings:
            keyboard = await create_bookings_keyboard(bookings, page=1)
            await callback.message.edit_text(
                f"✅ Бронирование отменено\n\n"
                f"📅 Ваши предстоящие консультации ({len(bookings)}/{settings.BOOKING_LIMIT}):",
                reply_markup=keyboard
            )
        else:
            await callback.message.edit_text(
                "✅ Бронирование отменено\n\n"
                f"У вас нет предстоящих консультаций.\n"
                f"Доступно записей: {settings.BOOKING_LIMIT}"
            )
    else:
        await callback.answer("❌ Не удалось отменить бронирование")

@consultation_router.callback_query(F.data == "back_to_bookings")
async def back_to_bookings_list(callback: CallbackQuery):
    user = get_user_by_chat_id(callback.from_user.id)
    bookings = get_user_bookings(user.id)
    keyboard = await create_bookings_keyboard(bookings, page=1)
    
    await callback.message.edit_text(
        f"📅 Ваши предстоящие консультации ({len(bookings)}/{settings.BOOKING_LIMIT}):",
        reply_markup=keyboard
    )

@consultation_router.callback_query(F.data.startswith("bookings_page_"))
async def process_bookings_page(callback: CallbackQuery):
    page = int(callback.data.split("_")[2])
    user = get_user_by_chat_id(callback.from_user.id)
    bookings = get_user_bookings(user.id)
    
    keyboard = await create_bookings_keyboard(bookings, page=page)
    await callback.message.edit_reply_markup(reply_markup=keyboard) 

@consultation_router.callback_query(F.data.startswith("cancel_"))
async def cancel_booking_creation(callback: CallbackQuery):
    from_date = datetime.now()
    to_date = from_date + timedelta(days=14)
    
    available_slots = get_available_slots(from_date, to_date)
    keyboard = await create_slots_keyboard(available_slots, page=1)
    
    await callback.message.edit_text(
        "Выберите удобное время для консультации:",
        reply_markup=keyboard
    ) 