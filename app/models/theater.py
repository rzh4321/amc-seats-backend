from sqlalchemy import (
    Column,
    Integer,
    String,
    CheckConstraint
)
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.showtime import Showtime
import pytz


class Theater(Base):
    __tablename__ = "theaters"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    timezone = Column(String(50), nullable=False)
    
    __table_args__ = (
        CheckConstraint(
            f"timezone = ANY(ARRAY{list(pytz.all_timezones)})",
            name="valid_timezone"
        ),
    )

    showtimes = relationship("Showtime", back_populates="theater")
