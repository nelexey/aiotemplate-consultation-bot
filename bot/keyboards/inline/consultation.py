from datetime import datetime
from typing import List, Tuple
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.database.models.slot import TimeSlot

def create_inline_keyboard(buttons: List[Tuple[str, str]], row_width: int = 2) -> InlineKeyboardMarkup:
    """
    Создает inline клавиатуру из списка кнопок
    :param buttons: список кнопок в формате [(text, callback_data), ...]
    :param row_width: количество кнопок в строке
    """
    builder = InlineKeyboardBuilder()
    
    for text, callback_data in buttons:
        builder.button(text=text, callback_data=callback_data)
    
    builder.adjust(row_width)
    return builder.as_markup()

async def create_slots_keyboard(slots: List[TimeSlot]) -> InlineKeyboardMarkup:
    buttons = []
    for slot in slots:
        button_text = slot.datetime.strftime("%d.%m.%Y %H:%M")
        callback_data = f"book_{slot.id}"
        buttons.append((button_text, callback_data))
    
    return create_inline_keyboard(buttons, row_width=1)

async def create_confirm_keyboard(slot_id: int) -> InlineKeyboardMarkup:
    buttons = [
        ("✅ Подтвердить", f"confirm_{slot_id}"),
        ("❌ Отменить", f"cancel_{slot_id}")
    ]
    return create_inline_keyboard(buttons, row_width=2) 