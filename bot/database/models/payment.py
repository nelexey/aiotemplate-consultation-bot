from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
from bot.database.main import Database

class Payment(Database.BASE):
    __tablename__ = 'payments'
    
    id = Column(Integer, primary_key=True)
    payment_id = Column(String(255), unique=True, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default='RUB')
    status = Column(String(20), nullable=False)  # pending, succeeded, canceled
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    paid_at = Column(DateTime, nullable=True)
    refunded = Column(Boolean, default=False)
    
    user_id = Column(Integer, ForeignKey('users.id'))
    slot_id = Column(Integer, ForeignKey('time_slots.id'))
    
    user = relationship("User", back_populates="payments")
    slot = relationship("TimeSlot", back_populates="payment")