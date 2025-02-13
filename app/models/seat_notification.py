from enum import Enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    func,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base import Base


class SeatNotification(Base):
    __tablename__ = "seat_notifications"

    id = Column(Integer, primary_key=True)
    user_email = Column(String(255), nullable=False)
    seat_number = Column(String(10), nullable=False)
    url = Column(String(60), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    show_date = Column(DateTime, nullable=False)


    __table_args__ = (UniqueConstraint("user_email", "url", "seat_number"),)
