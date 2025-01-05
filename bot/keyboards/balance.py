from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.misc.env import settings

DEPOSIT_AMOUNTS = [100, 500, 1000, 2000, 5000]

def get_balance_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Пополнить баланс", callback_data="deposit_balance")]
        ]
    )
    return keyboard

def get_deposit_keyboard() -> InlineKeyboardMarkup:
    keyboard = []
    
    # Add preset amounts
    for amount in DEPOSIT_AMOUNTS:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{amount} {settings.CURRENCY_SYMBOL}",
                callback_data=f"deposit_amount:{amount}"
            )
        ])
    
    # Add custom amount option
    keyboard.append([
        InlineKeyboardButton(text="Другая сумма", callback_data="deposit_custom")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard) 