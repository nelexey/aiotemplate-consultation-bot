from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import and_
from bot.database.main import Database
from bot.database.models.slot import TimeSlot
from bot.misc.env import settings

def get_available_slots(from_date: datetime, to_date: datetime) -> List[TimeSlot]:
    session = Database().session
    return session.query(TimeSlot).filter(
        and_(
            TimeSlot.datetime.between(from_date, to_date),
            TimeSlot.is_available == True,
            TimeSlot.status == 'available',
            TimeSlot.datetime > datetime.now()
        )
    ).all()

def book_slot(slot_id: int, user_id: int) -> bool:
    session = Database().session
    slot = session.query(TimeSlot).filter(TimeSlot.id == slot_id).first()
    
    if slot and slot.is_available and slot.datetime > datetime.now():
        slot.is_available = False
        slot.client_id = user_id
        slot.status = 'booked'
        session.commit()
        return True
    return False

def add_slot(slot_datetime: datetime) -> TimeSlot:
    session = Database().session
    new_slot = TimeSlot(datetime=slot_datetime)
    session.add(new_slot)
    session.commit()
    return new_slot 

def get_all_slots(from_date: datetime = None) -> List[TimeSlot]:
    session = Database().session
    query = session.query(TimeSlot)
    
    if from_date:
        query = query.filter(TimeSlot.datetime >= from_date)
    
    return query.order_by(TimeSlot.datetime).all()

def get_slot_by_id(slot_id: int) -> Optional[TimeSlot]:
    session = Database().session
    return session.query(TimeSlot).filter(TimeSlot.id == slot_id).first()

def get_booked_slots(datetime_check: datetime) -> List[TimeSlot]:
    session = Database().session
    return session.query(TimeSlot).filter(
        and_(
            TimeSlot.datetime >= datetime_check,
            TimeSlot.datetime < datetime_check + timedelta(hours=1),
            TimeSlot.is_available == False,
            TimeSlot.status == 'booked'
        )
    ).all() 

def get_user_bookings(user_id: int) -> List[TimeSlot]:
    session = Database().session
    return session.query(TimeSlot).filter(
        and_(
            TimeSlot.client_id == user_id,
            TimeSlot.status == 'booked',
            TimeSlot.datetime >= datetime.now()
        )
    ).order_by(TimeSlot.datetime).all() 

def check_user_booking_limit(user_id: int) -> bool:
    session = Database().session
    active_bookings = session.query(TimeSlot).filter(
        and_(
            TimeSlot.client_id == user_id,
            TimeSlot.status == 'booked',
            TimeSlot.datetime >= datetime.now()
        )
    ).count()
    
    return active_bookings < settings.BOOKING_LIMIT 

async def cancel_booking(slot_id: int, bot) -> bool:
    session = Database().session
    try:
        slot = session.query(TimeSlot).filter(TimeSlot.id == slot_id).first()
        if slot and slot.status == 'booked':
            time_until = slot.datetime - datetime.now()
            if time_until > timedelta(days=1):
                new_status = 'available'
                status_text = '🔓 слот снова доступен для записи'
                slot.is_available = True
            else:
                new_status = 'cancelled'
                status_text = '❌ слот отменён'
                slot.is_available = False
            
            client_username = slot.client.username or 'Без username'
            
            slot.status = new_status
            slot.client_id = None
            session.commit()
            
            try:
                await bot.send_message(
                    settings.admin_id,
                    f"ℹ️ Пользователь @{client_username} отменил консультацию\n"
                    f"📅 Дата: {slot.datetime.strftime('%d.%m.%Y %H:%M')}\n"
                    f"📌 Статус: {status_text}"
                )
            except Exception as e:
                print(f"Error sending message to admin: {str(e)}")
            
            return True
        return False
    except Exception as e:
        session.rollback()
        return False
    finally:
        session.close() 