import logging
import os
from typing import Optional
from sqlmodel import Field, Session, SQLModel, create_engine

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", "aarohi_intake.db")
sqlite_url = f"sqlite:///{DB_PATH}"

engine = create_engine(sqlite_url, echo=False)

class PatientIntake(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    age: int
    gender: str
    contact: str
    complaint: str
    duration: str
    severity: int
    medications: str
    conditions: str

def init_db():
    try:
        SQLModel.metadata.create_all(engine)
        logger.info(f"Database initialized via SQLModel at {DB_PATH}")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")

def save_intake(data: dict) -> bool:
    try:
        intake = PatientIntake(**data)
        with Session(engine) as session:
            session.add(intake)
            session.commit()
            session.refresh(intake)
        logger.info(f"Intake report for {data.get('name')} saved successfully.")
        return True
    except Exception as e:
        logger.error(f"Error saving intake to database: {e}")
        return False
