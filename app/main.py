from fastapi import FastAPI, Depends
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.seat_notification import SeatNotification
from datetime import date


# uvicorn app.main:app --reload

# Create FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://jnfnamjbpcmfhdfoboaennifodfmjmip"],
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
