from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

# -------------------------------
# Load environment variables
# -------------------------------
load_dotenv()

# -------------------------------
# Database credentials
# -------------------------------
DB_USER = os.getenv("DB_USER", "teamsync_db_1r29_user")        # Render DB username
DB_PASSWORD = os.getenv("DB_PASSWORD", "fQUCYQnAj8UIPGdBWvlFJV3fdF77duRk")  # Render DB password
DB_HOST = os.getenv("DB_HOST", "dpg-d2k7bqu3jp1c73ftoa60-a")  # Render hostname
DB_PORT = os.getenv("DB_PORT", "5432")                         # default PostgreSQL port
DB_NAME = os.getenv("DB_NAME", "teamsync_db_1r29")            # Render DB name

# -------------------------------
# URL-encode the password
# -------------------------------
encoded_password = quote_plus(DB_PASSWORD)

# -------------------------------
# Build SQLAlchemy Database URL
# -------------------------------
DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# -------------------------------
# Create SQLAlchemy engine
# -------------------------------
engine = create_engine(DATABASE_URL, echo=True)  # echo=True prints SQL queries for debugging

# -------------------------------
# Create session
# -------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# -------------------------------
# Base class for models
# -------------------------------
Base = declarative_base()

# -------------------------------
# Dependency for routes
# -------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
