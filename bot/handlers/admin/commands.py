from aiogram import Router
from aiogram.types import Message
from aiogram.filters.command import Command
from bot.filters.is_admin import IsAdmin
from bot.database.methods.users import create_user

commands_router = Router()

@commands_router.message(Command('start'), IsAdmin())
async def start_command(message: Message):
    # Создаем пользователя-админа при первом запуске
    create_user(message.from_user.id, message.from_user.username)
    
    await message.answer(
        "👋 Добро пожаловать в админ-панель!\n\n"
        "Доступные команды:\n"
        "/add_slot YYYY-MM-DD HH:MM - добавить новый слот\n"
        "/view_slots - просмотр всех слотов\n"
        "/schedule - просмотр доступных слотов (как у пользователя)"
    )