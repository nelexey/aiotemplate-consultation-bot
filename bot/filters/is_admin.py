from aiogram.filters import BaseFilter
from aiogram.types import Message
from bot.misc.env import settings

class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return str(message.from_user.id) in settings.ADMIN_IDS.split(',')
