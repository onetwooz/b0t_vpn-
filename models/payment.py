from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Payment(Base):
    __tablename__ = 'payments'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default='RUB')
    provider = Column(String)  # yookassa/telegram
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    details = Column(String)  # json/text
    user = relationship('User', backref='payments') 