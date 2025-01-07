from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from bot.keyboards.inline.menu import get_main_menu_keyboard
from bot.handlers.user.balance import show_balance
from bot.handlers.user.consultation import show_schedule, show_my_bookings

menu_router = Router()

@menu_router.message(Command("menu"))
async def show_menu(message: Message):
    """Показывает главное меню"""
    await message.answer(
        "Выберите действие:",
        reply_markup=get_main_menu_keyboard()
    )

@menu_router.callback_query(F.data == "menu_balance")
async def menu_balance(callback: CallbackQuery):
    await callback.answer()
    user = await show_balance(callback.message, edit=True)

@menu_router.callback_query(F.data == "menu_schedule")
async def menu_schedule(callback: CallbackQuery):
    await callback.answer()
    await show_schedule(callback.message, edit=True)

@menu_router.callback_query(F.data == "menu_bookings")
async def menu_bookings(callback: CallbackQuery):
    await callback.answer()
    await show_my_bookings(callback.message, edit=True)

@menu_router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "Выберите действие:",
        reply_markup=get_main_menu_keyboard()
    )