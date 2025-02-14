from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.seat_notification import SeatNotification
from app.models.theater import Theater
from app.models.movie import Movie
from app.models.showtime import Showtime
from sqlalchemy.sql import func


from datetime import date, datetime


# uvicorn app.main:app --reload

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "chrome-extension://jnfnamjbpcmfhdfoboaennifodfmjmip",
        "http://localhost:8000",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class NotificationRequest(BaseModel):
    email: str  # "email@gmail.com"
    seatNumbers: list[str]  # ['A1','A2']
    url: str
    showDate: date
    movie: str  # "Heart Eyes"
    theater: str  # "AMC Empire 25"
    showtime: str  # "7:45 pm"
    # are_specifically_requested: bool


@app.post("/notifications")
async def create_notification(
    request: NotificationRequest, db: Session = Depends(get_db)
):
    print(request)
    # check if theater exists
    existing_theater = (
        db.query(Theater)
        .filter(
            Theater.name == request.theater,
        )
        .first()
    )

    if not existing_theater:
        new_theater = Theater(name=request.theater)

        db.add(new_theater)
        db.commit()
        print(f"added new theater {request.theater} to db")
        theater_id = new_theater.id
    else:
        theater_id = existing_theater.id

    # check if movie already exists
    existing_movie = (
        db.query(Movie)
        .filter(
            Movie.name == request.movie,
        )
        .first()
    )

    if not existing_movie:
        new_movie = Movie(name=request.movie, last_detected=func.now())

        db.add(new_movie)
        print("NEW MOVIE")
        movie_id = new_movie.id
    else:
        movie_id = existing_movie.id
        existing_movie.last_detected = func.now()

    showtime_obj = datetime.strptime(request.showtime, "%I:%M %p").time()
    # Combine the date and time into a datetime object
    show_datetime = datetime.combine(request.showDate, showtime_obj)
    is_past = show_datetime < datetime.now()
    if is_past:
        print(f"SHOWTIME OBJ IS BEFORE TODAY: ", show_datetime)
        return {"error": "This movie showing no longer exists."}

    # we can now commit the new movie, if it didnt exist already
    db.commit()
    # check if showtime already exists
    existing_showtime = (
        db.query(Showtime)
        .filter(
            Showtime.movie_id == movie_id,
            Showtime.showtime == showtime_obj,
            Showtime.theater_id == theater_id,
            Showtime.show_date == request.showDate,
            Showtime.seating_url == request.url,
        )
        .first()
    )

    if not existing_showtime:
        new_showtime = Showtime(
            movie_id=movie_id,
            showtime=showtime_obj,
            theater_id=theater_id,
            show_date=request.showDate,
            seating_url=request.url,
        )

        db.add(new_showtime)
        print(f"NEW SHOWTIME")
        showtime_id = new_showtime.id
    else:
        showtime_id = existing_showtime.id

    # Check existing notifications for all requested seats
    all_exist = True
    new_notifications = []

    for seat_number in request.seatNumbers:
        existing_notification = (
            db.query(SeatNotification)
            .filter(
                SeatNotification.user_email == request.email,
                SeatNotification.seat_number == seat_number,
                SeatNotification.showtime_id == showtime_id,
            )
            .first()
        )

        if not existing_notification:
            all_exist = False
            new_notifications.append(
                SeatNotification(
                    user_email=request.email,
                    seat_number=seat_number,
                    showtime_id=showtime_id,
                    is_specifically_requested=False,
                )
            )

    if all_exist:
        print(f"ALL NOTIFS ALREADY EXIST")
        return {"exists": True}

    # Add new notifications
    for notification in new_notifications:
        db.add(notification)

    # commit the new showtime and notifs
    db.commit()
    print(f"ADDED NEW NOTIFS")

    return {
        "exists": False,
        "created": len(new_notifications),
        "total": len(request.seatNumbers),
    }


@app.get("/unsubscribe/{notification_id}", response_class=HTMLResponse)
async def unsubscribe(notification_id: int, db: Session = Depends(get_db)):
    notification = (
        db.query(SeatNotification)
        .filter(SeatNotification.id == notification_id)
        .first()
    )

    if not notification:
        return """
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 40px auto; text-align: center;">
                <h1>Invalid Link</h1>
                <p>This notification link is invalid or has already been deleted.</p>
            </body>
        </html>
        """

    try:
        db.delete(notification)
        db.commit()
        return """
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 40px auto; text-align: center;">
                <h1>Successfully Unsubscribed</h1>
                <p>You will no longer receive notifications for this seat.</p>
            </body>
        </html>
        """
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error deleting notification")
