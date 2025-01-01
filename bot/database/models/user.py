from sqlalchemy import Column, Integer, BigInteger, String
from sqlalchemy.orm import relationship
from bot.database.main import Database


class User(Database.BASE):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(255), nullable=True)
    
    # Добавляем связь с TimeSlot
    bookings = relationship("TimeSlot", back_populates="client")

