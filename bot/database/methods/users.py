from typing import Optional
from bot.database.main import Database
from bot.database.models.user import User

def create_user(chat_id: int, username: str = None) -> User:
    session = Database().session
    user = session.query(User).filter(User.chat_id == chat_id).first()
    if not user:
        user = User(chat_id=chat_id, username=username)
        session.add(user)
        session.commit()
    return user

def get_user_by_chat_id(chat_id: int) -> Optional[User]:
    session = Database().session
    return session.query(User).filter(User.chat_id == chat_id).first()