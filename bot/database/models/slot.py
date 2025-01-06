from sqlalchemy import Column, Integer, DateTime, Boolean, ForeignKey, String, Numeric
from sqlalchemy.orm import relationship
from bot.database.main import Database
from bot.misc.env import settings

class TimeSlot(Database.BASE):
    __tablename__ = 'time_slots'
    
    id = Column(Integer, primary_key=True)
    datetime = Column(DateTime, nullable=False)
    is_available = Column(Boolean, default=True)
    client_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    status = Column(String(50), default='available')  # available, booked, cancelled
    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default=lambda: settings.CURRENCY)
    
    client = relationship("User", back_populates="bookings")