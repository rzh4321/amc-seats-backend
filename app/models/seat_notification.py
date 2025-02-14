from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base


class SeatNotification(Base):
    __tablename__ = "seat_notifications"

    id = Column(Integer, primary_key=True)
    user_email = Column(String(255), nullable=False)
    seat_number = Column(String(20), nullable=False)
    showtime_id = Column(Integer, ForeignKey("showtimes.id"), nullable=False)
    last_notified = Column(DateTime(timezone=True), nullable=True)
    is_specifically_requested = Column(Boolean, nullable=False)

    showtime = relationship("Showtime", back_populates="seat_notifications")
