from aiogram.filters import BaseFilter
from aiogram.types import Message
from bot.misc.env import settings

class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in settings.admin_ids
