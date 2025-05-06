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
import pytz
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import smtplib
import logging
from datetime import date, datetime, timedelta, timezone

logger = logging.getLogger(__name__)

# uvicorn app.main:app --reload

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "chrome-extension://jnfnamjbpcmfhdfoboaennifodfmjmip",
        "chrome-extension://gcehgmpfomiadbpkllbhmckebodcjkbe",
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
    movie: str  # "Heart Eyes"
    theater: str  # "AMC Empire 25"
    showtime: datetime
    areSpecficallyRequested: bool


def send_email(
    to_email,
    seat_numbers,
    page_url,
    date_string,
    movie,
    theater,
    time_string,
    is_specifically_requested,
    showtime_id,
):
    # 500 emails per day
    password = os.getenv("app_password")
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "amcseatalert@gmail.com"

    all_notifications_url = f"https://amc-seats-backend.onrender.com/unsubscribe/{showtime_id}/{to_email}"

    intro = f"""You have requested to be notified for the following seats"""

    email_body = f"""
    <html>
    <head>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
        </style>
    </head>
    <body style="background-color: #1A1A1A; color: #FFFFFF; font-family: 'Inter', sans-serif; line-height: 1.6; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #222222; border-radius: 12px; overflow: hidden;">
            <div style="background-color: #000000; padding: 24px; text-align: center; border-bottom: 2px solid #333333;">
                <h1 style="color: #F5F5F5; font-size: 28px; margin: 0;">AMC Seat Alert</h1>
            </div>
            
            <div style="padding: 32px 24px;">
                <h2 style="color: #E21836; font-size: 24px; margin-bottom: 24px; text-align: center;">{intro}</h2>
                
                <div style="background-color: #2A2A2A; padding: 24px; border-radius: 8px; margin-bottom: 32px;">
                    <h3 style="color: #FFFFFF; font-size: 22px; margin-bottom: 16px; text-align: center;">{movie}</h3>
                    <p style="margin-bottom: 12px;"><span style="color: #999999;">Theater:</span> {theater}</p>
                    <p style="margin-bottom: 12px;"><span style="color: #999999;">Date:</span> {date_string}</p>
                    <p style="margin-bottom: 12px;"><span style="color: #999999;">Time:</span> {time_string}</p>
                    <p style="margin-bottom: 12px;"><span style="color: #999999;">Seat:</span> {', '.join(seat_numbers) if is_specifically_requested else 'Any'}</p>
                </div>

                <div style="text-align: center; margin-bottom: 32px;">
                    <a href="{page_url}" style="display: inline-block; background-color: #E21836; color: #FFFFFF; padding: 16px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Seating Map</a>
                </div>

                <div style="border-top: 1px solid #333333; padding-top: 24px;">
                    <p style="color: #999999; margin-bottom: 16px; text-align: center;">Didn't request this notification or changed your mind?</p>
                    
                    
                    <div style="text-align: center;">
                        <a href="{all_notifications_url}" style="display: inline-block; background-color: #333333; color: #FFFFFF; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-size: 14px;">Unsubscribe from this showing</a>
                    </div>
                </div>
            </div>
            
            <div style="background-color: #000000; padding: 16px; text-align: center;">
                <p style="color: #666666; font-size: 12px; margin: 0;">This email was sent automatically. Do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Notification Confirmation - {movie} at {theater}"
    msg["From"] = sender_email
    msg["To"] = to_email

    # Attach both plain text and HTML versions
    text_part = MIMEText(email_body.replace("<br>", "\n"), "plain")
    html_part = MIMEText(email_body, "html")
    msg.attach(text_part)
    msg.attach(html_part)

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, password)
            server.send_message(msg)
            logging.info(f"Email confirmation sent successfully to {to_email}")
            return True
    except Exception as e:
        logging.error(f"Error sending email confirmation: {str(e)}")
        return False


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
        return {"error": "This theater is not yet supported."}
    else:
        theater_id = existing_theater.id
        timezone = existing_theater.timezone

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
        db.commit()
        print("NEW MOVIE")
        movie_id = new_movie.id
    else:
        movie_id = existing_movie.id
        existing_movie.last_detected = func.now()

    now = datetime.now(pytz.UTC)
    is_past = request.showtime < now
    if is_past:
        print(f"SHOWTIME ({request.showtime}) IS BEFORE TODAY ({now})")
        return {"error": "This movie showing no longer exists."}
    # we can now commit the new movie, if it didnt exist already
    db.commit()
    # check if showtime already exists
    existing_showtime = (
        db.query(Showtime).filter(Showtime.seating_url == request.url).first()
    )

    if not existing_showtime:
        new_showtime = Showtime(
            movie_id=movie_id,
            showtime=request.showtime,
            theater_id=theater_id,
            seating_url=request.url,
        )

        print(f"NEW SHOWTIME")
        db.add(new_showtime)
        db.commit()
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
                    is_specifically_requested=request.areSpecficallyRequested,
                )
            )

    if all_exist:
        print(f"ALL NOTIFS ALREADY EXIST")
        return {"exists": True}

    # Add new notifications
    for notification in new_notifications:
        db.add(notification)

    # commit the new notifs
    db.commit()
    print(f"ADDED NEW NOTIFS")
    tz = pytz.timezone(timezone)
    local_datetime = request.showtime.astimezone(tz)
    # Format date like "Sunday, February 16, 2025"
    date_string = local_datetime.strftime("%A, %B %d, %Y")
    # Format time like "7:30 pm"
    time_string = local_datetime.strftime("%I:%M %p").lstrip("0").lower()

    send_email(
        request.email,
        request.seatNumbers,
        request.url,
        date_string,
        request.movie,
        request.theater,
        time_string,
        request.areSpecficallyRequested,
        showtime_id,
    )

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
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {
                    font-family: 'Segoe UI', Arial, sans-serif;
                    max-width: 600px;
                    margin: 40px auto;
                    text-align: center;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                .container {
                    background-color: white;
                    border-radius: 10px;
                    padding: 30px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #e63946;
                    margin-bottom: 20px;
                }
                p {
                    color: #495057;
                    line-height: 1.6;
                    margin-bottom: 20px;
                }
                .icon {
                    font-size: 48px;
                    margin-bottom: 20px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="icon">❌</div>
                <h1>Invalid Link</h1>
                <p>This unsubscribe link is invalid or has already been processed.</p>
            </div>
        </body>
        </html>
        """

    try:
        # Get showtime details for the success message
        showtime = (
            db.query(Showtime).filter(Showtime.id == notification.showtime_id).first()
        )
        movie = db.query(Movie).filter(Movie.id == showtime.movie_id).first()
        theater = db.query(Theater).filter(Theater.id == showtime.theater_id).first()

        timezone = theater.timezone
        movie_datetime = showtime.showtime
        # Convert UTC to specified timezone
        tz = pytz.timezone(timezone)
        local_datetime = movie_datetime.astimezone(tz)

        # Format date like "Sunday, February 16, 2025"
        date_string = local_datetime.strftime("%A, %B %d, %Y")

        # Format time like "7:30 pm"
        time_string = local_datetime.strftime("%I:%M %p").lstrip("0").lower()

        db.delete(notification)
        db.commit()

        return f"""
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    max-width: 600px;
                    margin: 40px auto;
                    text-align: center;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    background-color: white;
                    border-radius: 10px;
                    padding: 30px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #2ecc71;
                    margin-bottom: 20px;
                }}
                p {{
                    color: #495057;
                    line-height: 1.6;
                    margin-bottom: 20px;
                }}
                .movie-details {{
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 20px 0;
                    text-align: left;
                }}
                .icon {{
                    font-size: 48px;
                    margin-bottom: 20px;
                }}
                .seat-info {{
                    color: #666;
                    font-size: 0.9em;
                    margin-top: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="icon">✅</div>
                <h1>Successfully Unsubscribed</h1>
                <p>You have been unsubscribed from notifications for:</p>
                <div class="movie-details">
                    <p><strong>Movie:</strong> {movie.name}</p>
                    <p><strong>Theater:</strong> {theater.name}</p>
                    <p><strong>Date:</strong> {date_string}</p>
                    <p><strong>Time:</strong> {time_string}</p>
                    <p><strong>Seat:</strong> {notification.seat_number}</p>
                </div>
                <p class="seat-info">You will no longer receive notifications for this specific seat.</p>
            </div>
        </body>
        </html>
        """
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/unsubscribe/{showtime_id}/{email}", response_class=HTMLResponse)
async def unsubscribe(showtime_id: int, email: str, db: Session = Depends(get_db)):
    notifications = (
        db.query(SeatNotification)
        .filter(
            SeatNotification.showtime_id == showtime_id,
            SeatNotification.user_email == email,
        )
        .all()
    )

    if not notifications:
        return """
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {
                    font-family: 'Segoe UI', Arial, sans-serif;
                    max-width: 600px;
                    margin: 40px auto;
                    text-align: center;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                .container {
                    background-color: white;
                    border-radius: 10px;
                    padding: 30px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #e63946;
                    margin-bottom: 20px;
                }
                p {
                    color: #495057;
                    line-height: 1.6;
                    margin-bottom: 20px;
                }
                .icon {
                    font-size: 48px;
                    margin-bottom: 20px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="icon">❌</div>
                <h1>Invalid Link</h1>
                <p>This unsubscribe link is invalid or has already been processed.</p>
            </div>
        </body>
        </html>
        """

    try:
        # Get showtime details for the success message
        showtime = db.query(Showtime).filter(Showtime.id == showtime_id).first()
        movie = db.query(Movie).filter(Movie.id == showtime.movie_id).first()
        theater = db.query(Theater).filter(Theater.id == showtime.theater_id).first()

        timezone = theater.timezone
        movie_datetime = showtime.showtime
        # Convert UTC to specified timezone
        tz = pytz.timezone(timezone)
        local_datetime = movie_datetime.astimezone(tz)

        # Format date like "Sunday, February 16, 2025"
        date_string = local_datetime.strftime("%A, %B %d, %Y")

        # Format time like "7:30 pm"
        time_string = local_datetime.strftime("%I:%M %p").lstrip("0").lower()

        # Delete all notifications for this showtime/email combination
        for notification in notifications:
            db.delete(notification)
        db.commit()

        return f"""
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    max-width: 600px;
                    margin: 40px auto;
                    text-align: center;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    background-color: white;
                    border-radius: 10px;
                    padding: 30px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #2ecc71;
                    margin-bottom: 20px;
                }}
                p {{
                    color: #495057;
                    line-height: 1.6;
                    margin-bottom: 20px;
                }}
                .movie-details {{
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 20px 0;
                    text-align: left;
                }}
                .icon {{
                    font-size: 48px;
                    margin-bottom: 20px;
                }}
                .seats {{
                    color: #666;
                    font-size: 0.9em;
                    margin-top: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="icon">✅</div>
                <h1>Successfully Unsubscribed</h1>
                <p>You have been unsubscribed from all seat notifications for:</p>
                <div class="movie-details">
                    <p><strong>Movie:</strong> {movie.name}</p>
                    <p><strong>Theater:</strong> {theater.name}</p>
                    <p><strong>Date:</strong> {date_string}</p>
                    <p><strong>Time:</strong> {time_string}</p>
                </div>
                <p class="seats">Unsubscribed from {len(notifications)} seat notification{'s' if len(notifications) != 1 else ''}</p>
            </div>
        </body>
        </html>
        """
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
