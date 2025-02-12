from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Create engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # Enable connection pool "pre-ping" feature
    pool_size=5,  # Number of connections to keep open
    max_overflow=10,  # Max number of connections to create above pool_size
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except:
        # If there's an error
        db.rollback()
        raise
    finally:
        db.close()
