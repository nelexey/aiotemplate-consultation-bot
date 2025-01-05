from aiogram import Bot
from bot.misc.env import settings
from datetime import datetime

async def notify_admins_booking_cancelled(bot: Bot, slot_datetime: datetime, client_info: str):
    """Sends notification to admins about cancelled booking"""
    for admin_id in settings.admin_ids:
        try:
            await bot.send_message(
                admin_id,
                f"❌ Отменена консультация\n"
                f"📅 Дата: {slot_datetime.strftime('%d.%m.%Y %H:%M')}\n"
                f"👤 Клиент: {client_info}"
            )
        except Exception as e:
            print(f"Error notifying admin {admin_id}: {str(e)}") 