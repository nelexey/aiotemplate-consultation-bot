from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.misc.env import settings

def create_payment_status_keyboard(payment_id: str, payment_url: str) -> InlineKeyboardMarkup:
    """Создает клавиатуру с кнопками для оплаты и проверки статуса"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="💳 Перейти к оплате",
                url=f"{payment_url}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔄 Проверить статус оплаты",
                callback_data=f"check_payment_{payment_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Отменить",
                callback_data="cancel_payment"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard) 