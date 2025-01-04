from sqlalchemy import Column, Integer, DateTime, Boolean, ForeignKey, String
from sqlalchemy.orm import relationship
from bot.database.main import Database

class TimeSlot(Database.BASE):
    __tablename__ = 'time_slots'
    
    id = Column(Integer, primary_key=True)
    datetime = Column(DateTime, nullable=False)
    is_available = Column(Boolean, default=True)
    client_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    # Статусы слота:
    # available - доступен для бронирования
    # pending - ожидает оплаты
    # booked - забронирован (оплачен)
    # cancelled - отменен
    status = Column(String(50), default='available')
    
    client = relationship("User", back_populates="bookings") 
    payment = relationship("Payment", back_populates="slot")