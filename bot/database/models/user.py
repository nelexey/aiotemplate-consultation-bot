from sqlalchemy import Column, Integer, BigInteger, String, Numeric
from sqlalchemy.orm import relationship
from bot.database.main import Database


class User(Database.BASE):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(255), nullable=True)
    balance = Column(Numeric(10, 2), default=0.00, nullable=False)
    
    # Связи
    bookings = relationship("TimeSlot", back_populates="client")
    payments = relationship("Payment", back_populates="user")
    

