from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from bot.database.methods.read import get_booked_slots

async def send_reminder(bot, slot):
    await bot.send_message(
        slot.client.chat_id,
        f"Напоминаем о консультации через час, в {slot.datetime.strftime('%H:%M')}!"
    )

def setup_reminders(bot):
    scheduler = AsyncIOScheduler()
    
    async def check_upcoming_consultations():
        next_hour = datetime.now() + timedelta(hours=1)
        next_hour = next_hour.replace(minute=0, second=0, microsecond=0)
        
        slots = get_booked_slots(next_hour)
        for slot in slots:
            slot_hour = slot.datetime.replace(minute=0, second=0, microsecond=0)
            if slot_hour == next_hour:
                await send_reminder(bot, slot)
    
    scheduler.add_job(check_upcoming_consultations, 'interval', minutes=1)
    scheduler.start()