from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Use environment variable if available, otherwise default to docker-compose settings
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+psycopg2://grievance_user:strongpassword@localhost:5432/grievance_db"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
