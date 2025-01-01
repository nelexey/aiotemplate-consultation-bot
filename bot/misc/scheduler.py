from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from bot.database.methods.slots import get_booked_slots

async def send_reminder(bot, slot):
    await bot.send_message(
        slot.client.chat_id,
        f"Напоминаем о консультации завтра в {slot.datetime.strftime('%H:%M')}!"
    )

def setup_reminders(bot):
    scheduler = AsyncIOScheduler()
    
    async def check_upcoming_consultations():
        tomorrow = datetime.now() + timedelta(days=1)
        slots = get_booked_slots(tomorrow)
        for slot in slots:
            await send_reminder(bot, slot)
    
    scheduler.add_job(check_upcoming_consultations, 'cron', hour=10)  # Отправка в 10:00
    scheduler.start()