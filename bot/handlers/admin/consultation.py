from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from datetime import datetime
from bot.filters.is_admin import IsAdmin
from bot.database.methods.slots import add_slot, get_all_slots

admin_consultation_router = Router()

@admin_consultation_router.message(Command("add_slot"), IsAdmin())
async def add_new_slot(message: Message):
    try:
        _, date_str, time_str = message.text.split()
        slot_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        
        new_slot = add_slot(slot_datetime)
        await message.answer(f"✅ Добавлен новый слот: {slot_datetime.strftime('%d.%m.%Y %H:%M')}")
    except Exception as e:
        await message.answer("❌ Ошибка при добавлении слота. Используйте формат: /add_slot YYYY-MM-DD HH:MM")

@admin_consultation_router.message(Command("view_slots"), IsAdmin())
async def view_slots(message: Message):
    from_date = datetime.now()
    slots = get_all_slots(from_date)
    
    if not slots:
        await message.answer("Нет доступных слотов.")
        return
    
    response = "📅 Список всех слотов:\n\n"
    for slot in slots:
        status = "✅ Занят" if not slot.is_available else "🔓 Свободен"
        slot_info = f"{slot.datetime.strftime('%d.%m.%Y %H:%M')} - {status}"
        
        if not slot.is_available and slot.client:
            slot_info += f"\nЗабронировал: @{slot.client.username or 'Без username'}"
        
        response += f"{slot_info}\n\n"
    
    await message.answer(response)