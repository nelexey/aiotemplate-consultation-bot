from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import and_
from bot.database.main import Database
from bot.database.models.slot import TimeSlot

def get_available_slots(from_date: datetime, to_date: datetime) -> List[TimeSlot]:
    session = Database().session
    return session.query(TimeSlot).filter(
        and_(
            TimeSlot.datetime.between(from_date, to_date),
            TimeSlot.is_available == True
        )
    ).all()

def book_slot(slot_id: int, user_id: int) -> bool:
    session = Database().session
    slot = session.query(TimeSlot).filter(TimeSlot.id == slot_id).first()
    
    if slot and slot.is_available:
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