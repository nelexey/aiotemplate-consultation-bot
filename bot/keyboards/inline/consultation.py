from datetime import datetime
from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.database.models.slot import TimeSlot

SLOTS_PER_PAGE = 7

async def create_slots_keyboard(slots: List[TimeSlot], page: int = 1) -> InlineKeyboardMarkup:
    total_pages = (len(slots) + SLOTS_PER_PAGE - 1) // SLOTS_PER_PAGE
    start_idx = (page - 1) * SLOTS_PER_PAGE
    end_idx = start_idx + SLOTS_PER_PAGE
    slot_buttons = [
        [InlineKeyboardButton(
            text=slot.datetime.strftime("%d.%m.%Y %H:%M"),
            callback_data=f"book_{slot.id}"
        )]
        for slot in slots[start_idx:end_idx]
    ]
    
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="◀️", callback_data=f"page_{page-1}"))
    nav_row.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="current_page"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton(text="▶️", callback_data=f"page_{page+1}"))
    
    keyboard = slot_buttons + ([nav_row] if nav_row else [])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def create_confirm_keyboard(slot_id: int) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_{slot_id}"),
            InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_{slot_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)