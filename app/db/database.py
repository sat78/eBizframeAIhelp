from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

from urllib.parse import quote_plus

load_dotenv()

# PostgreSQL Connection String
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    # Default fallback causing potential error with special chars
    password = quote_plus("Ess@1234")
    SQLALCHEMY_DATABASE_URL = f"postgresql://postgres:{password}@localhost/videoDatabase"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
