from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.seat_notification import SeatNotification
from datetime import date


# uvicorn app.main:app --reload

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "chrome-extension://jnfnamjbpcmfhamfoboaennifodfmjmip",
        "*" 
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class NotificationRequest(BaseModel):
    email: str
    seatNumber: str
    url: str
    showDate: date


@app.post("/notifications")
async def create_notification(
    request: NotificationRequest, db: Session = Depends(get_db)
):
    print(request)
    # Check if notification already exists
    existing_notification = (
        db.query(SeatNotification)
        .filter(
            SeatNotification.user_email == request.email,
            SeatNotification.seat_number == request.seatNumber,
            SeatNotification.url == request.url,
        )
        .first()
    )
    print(f"EXISATING NOTIF: ${existing_notification}")
    if existing_notification:
        return {"exists": True}

    new_notification = SeatNotification(
        user_email=request.email,
        seat_number=request.seatNumber,
        url=request.url,
        show_date=request.showDate,
    )

    db.add(new_notification)
    db.commit()

    return {"exists": False}


@app.get("/unsubscribe/{notification_id}", response_class=HTMLResponse)
async def unsubscribe(notification_id: int, db: Session = Depends(get_db)):
    notification = db.query(SeatNotification).filter(SeatNotification.id == notification_id).first()
    
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