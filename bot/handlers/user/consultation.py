from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from datetime import datetime, timedelta

from bot.database.methods.slots import get_available_slots, book_slot, get_slot_by_id, get_user_bookings
from bot.keyboards.inline.consultation import create_slots_keyboard, create_confirm_keyboard
from bot.database.methods.users import get_user_by_chat_id

consultation_router = Router()

@consultation_router.message(Command("schedule"))
async def show_schedule(message: Message):
    from_date = datetime.now()
    to_date = from_date + timedelta(days=14)
    
    available_slots = get_available_slots(from_date, to_date)
    if not available_slots:
        await message.answer("К сожалению, нет доступных слотов для записи.")
        return
    
    keyboard = await create_slots_keyboard(available_slots)
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
    if not bookings:
        await message.answer("У вас нет предстоящих консультаций.")
        return
    
    response = "📅 Ваши предстоящие консультации:\n\n"
    for booking in bookings:
        time_until = booking.datetime - datetime.now()
        hours_left = int(time_until.total_seconds() / 3600)
        
        if hours_left < 1:
            minutes_left = int(time_until.total_seconds() / 60)
            time_info = f"через {minutes_left} минут"
        else:
            time_info = f"через {hours_left} часов"
            
        response += (
            f"🕐 {booking.datetime.strftime('%d.%m.%Y %H:%M')}\n"
            f"⏳ Начнется {time_info}\n\n"
        )
    
    await message.answer(response) 