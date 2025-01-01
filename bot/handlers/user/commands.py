from aiogram import Router
from aiogram.types import Message
from aiogram.filters.command import Command
from bot.database.methods.users import create_user

commands_router = Router()

@commands_router.message(Command('start'))
async def start_command(message: Message):
    # Создаем пользователя при первом запуске
    create_user(message.from_user.id, message.from_user.username)
    
    await message.answer(
        "👋 Добро пожаловать в бот записи на консультации!\n\n"
        "Доступные команды:\n"
        "/schedule - посмотреть доступные слоты для записи\n"
        "/my_bookings - мои записи на консультации"
    )