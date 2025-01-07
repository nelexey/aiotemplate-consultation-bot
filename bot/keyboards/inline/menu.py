from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру главного меню"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="📅 Записаться на консультацию",
                callback_data="menu_schedule"
            )
        ],
        [
            InlineKeyboardButton(
                text="💳 Баланс",
                callback_data="menu_balance"
            )
        ],
        [
            InlineKeyboardButton(
                text="📋 Мои записи",
                callback_data="menu_bookings"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру с кнопкой возврата в меню"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="◀️ Вернуться в меню",
                callback_data="back_to_menu"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard) 