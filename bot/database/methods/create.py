from sqlalchemy.exc import NoResultFound
from bot.database.main import Database
from bot.database.models.user import User
from bot.database.models.payment import Payment
from bot.database.models.slot import TimeSlot
from datetime import datetime
from bot.misc.env import settings

def create_user(chat_id: int, username: str) -> User:
    """Creates a new user in the database"""
    session = Database().session
    try:
        user = User(
            chat_id=chat_id,
            username=username,
        )
        session.add(user)
        session.commit()
        return user
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def create_payment(
    payment_id: str,
    amount: float,
    currency: str,
    status: str,
    user_id: int,
) -> Payment:
    """Creates a new payment record"""
    session = Database().session
    try:
        payment = Payment(
            payment_id=payment_id,
            amount=amount,
            currency=currency,
            status=status,
            user_id=user_id,
        )
        session.add(payment)
        session.commit()
        return payment
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def create_slot(slot_datetime: datetime, price: float) -> TimeSlot:
    """Creates a new time slot"""
    session = Database().session
    try:
        new_slot = TimeSlot(
            datetime=slot_datetime,
            price=price,
            currency=settings.CURRENCY
        )
        session.add(new_slot)
        session.commit()
        return new_slot
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()