from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy import and_
from sqlalchemy.orm import joinedload
from bot.database.main import Database
from bot.database.models.user import User
from bot.database.models.payment import Payment
from bot.database.models.slot import TimeSlot

def get_user_by_chat_id(chat_id: int) -> Optional[User]:
    """Gets user by chat ID"""
    session = Database().session
    try:
        return session.query(User).filter(User.chat_id == chat_id).first()
    finally:
        session.close()

def get_all_user_payments(user_id: int) -> Optional[List[Payment]]:
    """Gets all payments for a user"""
    session = Database().session
    try:
        return session.query(Payment).filter(Payment.user_id == user_id).all()
    finally:
        session.close()

def get_available_slots(from_date: datetime, to_date: datetime) -> List[TimeSlot]:
    """Gets available time slots between two dates"""
    session = Database().session
    try:
        return session.query(TimeSlot).filter(
            and_(
                TimeSlot.datetime.between(from_date, to_date),
                TimeSlot.is_available == True,
                TimeSlot.status == 'available',
                TimeSlot.datetime > datetime.now()
            )
        ).order_by(TimeSlot.datetime).all()
    finally:
        session.close()

def get_slot_by_id(slot_id: int) -> Optional[TimeSlot]:
    """Gets time slot by ID"""
    session = Database().session
    try:
        return session.query(TimeSlot).filter(TimeSlot.id == slot_id).first()
    finally:
        session.close()

def get_user_bookings(user_id: int) -> List[TimeSlot]:
    """Gets all bookings for a user"""
    session = Database().session
    try:
        return session.query(TimeSlot).filter(
            and_(
                TimeSlot.client_id == user_id,
                TimeSlot.status.in_(['booked', 'cancelled']),
                TimeSlot.datetime >= datetime.now()
            )
        ).order_by(TimeSlot.datetime).all()
    finally:
        session.close()

def get_all_slots(from_date: datetime = None) -> List[TimeSlot]:
    """Gets all time slots"""
    session = Database().session
    try:
        query = session.query(TimeSlot)
        if from_date:
            query = query.filter(TimeSlot.datetime >= from_date)
        return query.order_by(TimeSlot.datetime).all()
    finally:
        session.close()

def check_user_booking_limit(user_id: int, limit: int) -> bool:
    """Checks if user has reached booking limit"""
    session = Database().session
    try:
        active_bookings = session.query(TimeSlot).filter(
            and_(
                TimeSlot.client_id == user_id,
                TimeSlot.datetime >= datetime.now(),
                TimeSlot.status.in_(['booked', 'cancelled'])
            )
        ).count()
        return active_bookings < limit
    finally:
        session.close()

def get_booked_slots(datetime_check: datetime) -> List[TimeSlot]:
    """Gets all booked slots for a specific datetime"""
    session = Database().session
    try:
        return session.query(TimeSlot).filter(
            and_(
                TimeSlot.status == 'booked',
                TimeSlot.datetime >= datetime_check,
                TimeSlot.datetime < datetime_check + timedelta(hours=1)
            )
        ).all()
    finally:
        session.close()

def count_active_payments(user_id: int, minutes: int = 10) -> int:
    """
    Подсчитывает количество активных (pending) платежей пользователя
    
    Args:
        user_id: ID пользователя
        minutes: За сколько последних минут проверять платежи (по умолчанию 10)
    """
    session = Database().session
    try:
        time_ago = datetime.now() - timedelta(minutes=minutes)
        return session.query(Payment).filter(
            and_(
                Payment.user_id == user_id,
                Payment.status == 'pending',
                Payment.created_at >= time_ago
            )
        ).count()
    finally:
        session.close()

def get_payment(payment_id: str) -> Optional[Payment]:
    """Gets payment by payment ID with user data"""
    session = Database().session
    return session.query(Payment).options(
        joinedload(Payment.user)
    ).filter(Payment.payment_id == payment_id).first()

