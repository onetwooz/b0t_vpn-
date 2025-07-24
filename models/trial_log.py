from sqlalchemy import Column, Integer, DateTime, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class TrialLog(Base):
    __tablename__ = 'trial_logs'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    server = Column(String)  # germany/usa
    issued_at = Column(DateTime, default=datetime.utcnow)
    user = relationship('User', backref='trial_logs') 