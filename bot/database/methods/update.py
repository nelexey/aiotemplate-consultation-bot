from datetime import datetime
from sqlalchemy.exc import NoResultFound
from bot.database.main import Database
from bot.database.models.user import User
from typing import Optional
from bot.database.models.payment import Payment



def update_user(chat_id: int, username: Optional[str] = None) -> bool:
    """
    Updates the specified fields of a user record in the database by chat_id.

    Args:
        chat_id (int): The unique identifier for the user from Telegram.
        username (Optional[str]): The new username to set for the user, if provided.

    Returns:
        bool: True if the user was found and updated successfully, False if the user was not found.

    This template demonstrates updating user data, with flexibility to modify multiple fields.
    """
    session = Database().session

    try:
        # Locate the user by chat_id
        user = session.query(User).filter(User.chat_id == chat_id).one()

        # Update fields if new values are provided
        if username is not None:
            user.username = username

        # Commit changes
        session.commit()
        return True

    except NoResultFound:
        # Return False if the user does not exist in the database
        return False

    finally:
        session.close()

def update_payment_status(payment_id: str, status: str, paid_at: Optional[datetime] = None) -> bool:
    """Обновление статуса платежа"""
    session = Database().session
    try:
        payment = session.query(Payment).filter_by(payment_id=payment_id).first()
        if not payment:
            return False
            
        payment.status = status
        if status == 'succeeded' and paid_at:
            payment.paid_at = paid_at
            
        session.commit()
        return True
    except Exception:
        session.rollback()
        return False
    finally:
        session.close()