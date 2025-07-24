from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import enum

class ServerLocation(enum.Enum):
    germany = 'germany'
    usa = 'usa'

class Key(Base):
    __tablename__ = 'keys'
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False)
    server = Column(Enum(ServerLocation), nullable=False)
    is_trial = Column(Boolean, default=False)
    issued_to = Column(Integer, ForeignKey('users.id'), nullable=True)
    issued_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    used = Column(Boolean, default=False)
    user = relationship('User', backref='keys') 