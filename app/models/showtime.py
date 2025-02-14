from sqlalchemy import Column, Integer, String, ForeignKey, Date, Time
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.movie import Movie


class Showtime(Base):
    __tablename__ = "showtimes"

    id = Column(Integer, primary_key=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    theater_id = Column(Integer, ForeignKey("theaters.id"), nullable=False)
    show_date = Column(Date, nullable=False)
    showtime = Column(Time, nullable=False)
    seating_url = Column(String(60), nullable=False)

    movie = relationship("Movie", back_populates="showtimes")
    theater = relationship("Theater", back_populates="showtimes")
    seat_notifications = relationship("SeatNotification", back_populates="showtime")
