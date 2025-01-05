from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from datetime import datetime
from bot.filters.is_admin import IsAdmin
from bot.database.methods.create import create_slot
from bot.database.methods.read import get_all_slots
from bot.misc.env import settings

admin_consultation_router = Router()

@admin_consultation_router.message(Command("add_slot"), IsAdmin())
async def add_new_slot(message: Message):
    try:
        _, date_str, time_str, price = message.text.split()
        slot_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        price = float(price)
        
        new_slot = create_slot(slot_datetime, price)
        await message.answer(
            f"✅ Добавлен новый слот:\n"
            f"📅 Дата: {slot_datetime.strftime('%d.%m.%Y %H:%M')}\n"
            f"💰 Цена: {price} {settings.CURRENCY_SYMBOL}"
        )
    except Exception as e:
        await message.answer(
            "❌ Ошибка при добавлении слота.\n"
            "Используйте формат: /add_slot YYYY-MM-DD HH:MM PRICE\n"
            "Например: /add_slot 2024-03-20 15:00 1500"
        )

@admin_consultation_router.message(Command("view_slots"), IsAdmin())
async def view_slots(message: Message):
    from_date = datetime.now()
    slots = get_all_slots(from_date)
    
    if not slots:
        await message.answer("Нет доступных слотов.")
        return
    
    response = "📅 Список всех слотов:\n\n"
    for slot in slots:
        status_map = {
            'available': '🔓 Свободен',
            'booked': '✅ Забронирован',
            'cancelled': '❌ Отменён'
        }
        status = status_map.get(slot.status, '❓ Неизвестно')
        slot_info = f"{slot.datetime.strftime('%d.%m.%Y %H:%M')} - {status}"
        
        if slot.status == 'booked' and slot.client:
            slot_info += f"\nЗабронировал: @{slot.client.username or 'Без username'}"
        
        response += f"{slot_info}\n\n"
    
    await message.answer(response)