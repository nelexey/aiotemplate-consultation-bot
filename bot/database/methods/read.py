from typing import Optional, List
from sqlalchemy.exc import NoResultFound
from bot.database.main import Database
from bot.database.models.user import User
from bot.database.models.payment import Payment
from bot.database.models.slot import TimeSlot


def get_user(chat_id: int) -> Optional[User]:
    """
    Retrieves a user by their chat_id from the database.

    Args:
        chat_id (int): The unique identifier for the user from Telegram.

    Returns:
        Optional[User]: The user object if found; otherwise, None.

    This template demonstrates a basic approach to querying a user by `chat_id`.
    """
    try:
        # Query for a user by chat_id
        return Database().session.query(User).filter(User.chat_id == chat_id).one()
    except NoResultFound:
        # Return None if no user is found
        return None

def get_payment_by_id(payment_id: str) -> Optional[Payment]:
    """Получение платежа по ID"""
    session = Database().session
    try:
        return session.query(Payment).filter_by(payment_id=payment_id).first()
    finally:
        session.close()

def get_user_payments(user_id: int) -> List[Payment]:
    """Получение всех платежей пользователя"""
    session = Database().session
    try:
        return session.query(Payment).filter_by(user_id=user_id).all()
    finally:
        session.close()

def get_payment_by_slot(slot_id: int, user_id: int, status: str = None) -> Optional[Payment]:
    """Получение платежа по ID слота и пользователя"""
    session = Database().session
    try:
        query = session.query(Payment).filter_by(slot_id=slot_id, user_id=user_id)
        if status:
            query = query.filter_by(status=status)
        return query.first()
    finally:
        session.close()

def get_slot_by_id(slot_id: int) -> Optional[TimeSlot]:
    """Получение слота по ID"""
    session = Database().session
    try:
        return session.query(TimeSlot).filter_by(id=slot_id).first()
    finally:
        session.close()