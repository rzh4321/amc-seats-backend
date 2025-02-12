from sqlalchemy import Column, Integer, Time, func, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base


# a showtime for a format for a movie in a theater on a date
class Showtime(Base):
    __tablename__ = "showtimes"

    id = Column(Integer, primary_key=True)
    movie_format_id = Column(
        Integer, ForeignKey("movie_formats.id", ondelete="CASCADE")
    )
    show_time = Column(Time, nullable=False)

    movie_format = relationship("MovieFormat", back_populates="showtimes")
    seat_notifications = relationship("SeatNotification", back_populates="showtime")

    __table_args__ = (UniqueConstraint("movie_format_id", "show_time"),)
