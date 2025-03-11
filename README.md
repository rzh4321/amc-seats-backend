# AMC SeatAlert Backend

FastAPI server of the [AMC SeatAlert Chrome extension](https://chromewebstore.google.com/detail/amc-seatalert/gcehgmpfomiadbpkllbhmckebodcjkbe?hl=en&authuser=0). This server handles seat notification requests and manages the PostgreSQL database for seat availability monitoring.

## Overview

This backend server provides a REST API endpoint that:

- Accepts notification requests from the [AMC SeatAlert Chrome extension](https://github.com/rzh4321/amc-seats)
- Manages seat notification subscriptions in a PostgreSQL database
- Prevents duplicate notification requests

## Prerequisites

- Python 3.8+
- PostgreSQL
- pip (Python package manager)

## Environment Setup

1. Create a `.env` file in the root directory to contain the connection string to your database: 

```.env
DATABASE_URL=postgresql://username:password@localhost:5432/database_name
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Project Structure

```txt
amc-seats-backend/
├── app/
│   ├── db/
│   │   ├── base.py         # SQLAlchemy Base configuration
│   │   └── session.py      # Database session management
│   ├── models/
│   │   └── seat_notification.py    # Database models
│   └── main.py             # FastAPI application and routes
├── .env                    # Environment variables (not committed)
└── requirements.txt        # Project dependencies
```

## Running the Server

Start the development server:

```bash
uvicorn app.main:app --reload
```

The server will run at `http://127.0.0.1:8000`

## API Endpoints

### POST /notifications

Creates a new seat notification subscription.

Request body:

```json
{
    "email": "user@gmail.com",
    "seatNumber": "D5",
    "url": "https://www.amctheatres.com/showtimes/129694401/seats",
    "showDate": "2025-02-12"
}
```

Response:

```json
{
    "exists": false
}
```

## Related Components

This server is part of a larger system:

- [AMC Seat Checker Chrome Extension](https://github.com/rzh4321/amc-seats)

## Development

1. Clone the repository:

```bash
git clone https://github.com/rzh4321/amc-seats-backend.git
```

1. Follow the setup instructions above
2. Make your changes
3. Test the API using the chrome extension or tools like Postman or curl

## Security Notes

- The CORS configuration is set to accept requests only from the Chrome extension

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License

## Contact

- [GitHub](https://github.com/rzh4321)
- [Email](rzh4321@gmail.com)
