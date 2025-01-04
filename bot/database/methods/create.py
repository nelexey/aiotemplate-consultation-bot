from sqlalchemy.exc import NoResultFound
from bot.database.main import Database
from bot.database.models.user import User
from bot.database.models.payment import Payment


def create_user(chat_id: int, username: str) -> None:
    """
    Adds a new user to the database if the user does not already exist.

    Args:
        chat_id (int): Unique identifier for the user from Telegram.
        username (str): Username of the user on Telegram.

    This function provides a basic template for adding a user. It checks
    if a user with the given chat_id already exists. If not, it creates a new user entry.
    """
    session = Database().session

    try:
        # Attempt to find an existing user by chat_id
        session.query(User.chat_id).filter(User.chat_id == chat_id).one()

    except NoResultFound:
        # If user does not exist, create a new entry
        new_user = User(
            chat_id=chat_id,
            username=username,
        )
        session.add(new_user)
        session.commit()


def create_payment(
    payment_id: str,
    amount: float,
    currency: str,
    status: str,
    user_id: int,
    slot_id: int
) -> Payment:
    """Создание записи о платеже"""
    session = Database().session
    try:
        payment = Payment(
            payment_id=payment_id,
            amount=amount,
            currency=currency,
            status=status,
            user_id=user_id,
            slot_id=slot_id
        )
        session.add(payment)
        session.commit()
        return payment
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()