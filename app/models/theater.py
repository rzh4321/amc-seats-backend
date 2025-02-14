from sqlalchemy import (
    Column,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.showtime import Showtime


class Theater(Base):
    __tablename__ = "theaters"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)

    showtimes = relationship("Showtime", back_populates="theater")
