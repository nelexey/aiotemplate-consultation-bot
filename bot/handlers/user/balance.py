from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.database.methods.read import get_user_by_chat_id
from bot.services.yookassa_service import YookassaService
from bot.misc.env import settings
from bot.keyboards.inline.balance import get_balance_keyboard, get_deposit_keyboard

router = Router()

class DepositStates(StatesGroup):
    waiting_for_amount = State()

@router.message(Command("balance"))
async def show_balance(message: Message):
    user = get_user_by_chat_id(message.chat.id)
    
    text = (f"💰 Ваш текущий баланс: {user.balance} {settings.CURRENCY_SYMBOL}\n"
            f"Валюта баланса: {user.currency}")
    
    await message.answer(text, reply_markup=get_balance_keyboard())

@router.callback_query(F.data == "deposit_balance")
async def deposit_balance(callback: CallbackQuery):
    await callback.message.edit_text(
        "Выберите сумму пополнения или введите свою:",
        reply_markup=get_deposit_keyboard()
    )

async def process_deposit(amount: float, chat_id: int, message_obj):
    """
    Общая функция для обработки пополнения баланса
    :param amount: Сумма пополнения
    :param chat_id: ID чата пользователя
    :param message_obj: Объект сообщения или callback query для ответа
    """
    if amount <= 0:
        await message_obj.answer("Сумма должна быть больше 0")
        return False

    if amount > settings.MAX_DEPOSIT_AMOUNT:
        await message_obj.answer(f"Максимальная сумма пополнения - {settings.MAX_DEPOSIT_AMOUNT:,.0f} {settings.CURRENCY_SYMBOL}")
        return False

    user = get_user_by_chat_id(chat_id)
    payment = YookassaService().create_payment(
        user_id=user.id,
        amount=amount,
        currency=user.currency,
        description="Пополнение баланса",
        return_url=settings.YOOKASSA_RETURN_URL,
    )

    text = f"Для пополнения баланса на сумму {amount} {settings.CURRENCY_SYMBOL} нажмите на кнопку ниже:"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="Оплатить",
                url=payment.confirmation.confirmation_url
            )
        ]]
    )

    if isinstance(message_obj, CallbackQuery):
        await message_obj.message.edit_text(text, reply_markup=keyboard)
    else:
        await message_obj.answer(text, reply_markup=keyboard)
    
    return True

@router.callback_query(F.data.startswith("deposit_amount:"))
async def process_deposit_amount(callback: CallbackQuery):
    amount = float(callback.data.split(":")[1])
    await process_deposit(amount, callback.message.chat.id, callback)

@router.callback_query(F.data == "deposit_custom")
async def ask_custom_amount(callback: CallbackQuery, state: FSMContext):
    await state.set_state(DepositStates.waiting_for_amount)
    await callback.message.edit_text(
        f"Введите сумму для пополнения в {settings.CURRENCY}:"
    )

@router.message(DepositStates.waiting_for_amount)
async def process_custom_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
        if await process_deposit(amount, message.chat.id, message):
            await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму числом") 