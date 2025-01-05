from typing import Optional
from sqlalchemy.exc import NoResultFound
from bot.database.main import Database
from bot.database.models.user import User
from bot.database.models.slot import TimeSlot
from bot.database.models.payment import Payment
from datetime import datetime
from aiogram import Bot
from sqlalchemy import and_
from bot.misc.env import settings

def update_user(chat_id: int, username: Optional[str] = None) -> bool:
    """Updates user information"""
    session = Database().session
    try:
        user = session.query(User).filter(User.chat_id == chat_id).one()
        if username is not None:
            user.username = username
        session.commit()
        return True
    except NoResultFound:
        return False
    finally:
        session.close()

def update_payment_status(payment_id: str, status: str, paid_at: Optional[datetime] = None) -> bool:
    """Updates payment status and paid_at time"""
    session = Database().session
    payment = session.query(Payment).filter(Payment.payment_id == payment_id).first()
    if not payment:
        return False
    
    payment.status = status
    if paid_at:
        payment.paid_at = paid_at
    
    session.commit()
    return True

def update_user_balance(user_id: int, new_balance: float) -> bool:
    """Updates user balance"""
    session = Database().session
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    
    user.balance = new_balance
    session.commit()
    return True

def book_slot(slot_id: int, user_id: int) -> bool:
    """Updates slot status to booked"""
    session = Database().session
    try:
        slot = session.query(TimeSlot).filter(TimeSlot.id == slot_id).first()
        if slot and slot.is_available and slot.datetime > datetime.now():
            slot.is_available = False
            slot.client_id = user_id
            slot.status = 'booked'
            session.commit()
            return True
        return False
    finally:
        session.close()

def cancel_booking(slot_id: int) -> bool:
    """Cancels a booking"""
    session = Database().session
    try:
        slot = session.query(TimeSlot).filter(TimeSlot.id == slot_id).first()
        if not slot or slot.status != 'booked':
            return False

        slot.status = 'cancelled'
        slot.is_available = True
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error cancelling booking: {str(e)}")
        return False
    finally:
        session.close()

def release_slot(slot_id: int) -> bool:
    """Releases a slot back to available state"""
    session = Database().session
    try:
        slot = session.query(TimeSlot).filter(TimeSlot.id == slot_id).first()
        if not slot or slot.status != 'booked':
            return False
            
        slot.status = 'available'
        slot.is_available = True
        slot.client_id = None
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error releasing slot: {str(e)}")
        return False
    finally:
        session.close()
