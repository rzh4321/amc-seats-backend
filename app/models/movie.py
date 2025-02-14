from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    func,
)
from sqlalchemy.orm import relationship
from app.db.base import Base


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    last_detected = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    showtimes = relationship("Showtime", back_populates="movie")
