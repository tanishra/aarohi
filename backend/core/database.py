import logging
import os
from typing import Optional
from sqlmodel import Field, Session, SQLModel, create_engine
from .encryption import encrypt_data, decrypt_data

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
        # Encrypt PII before creating the model
        encrypted_data = data.copy()

        # We encrypt name and contact. Complaint might also be considered PHI depending on strictness.
        if "name" in encrypted_data:
            encrypted_data["name"] = encrypt_data(str(encrypted_data["name"]))
        if "contact" in encrypted_data:
            encrypted_data["contact"] = encrypt_data(str(encrypted_data["contact"]))

        intake = PatientIntake(**encrypted_data)
        with Session(engine) as session:
            session.add(intake)
            session.commit()
            session.refresh(intake)

        logger.info(f"Intake report saved successfully. PII data was encrypted.")
        return True
    except Exception as e:
        logger.error(f"Error saving intake to database: {e}")
        return False

def get_intake(intake_id: int) -> Optional[dict]:
    """Helper method to retrieve and decrypt an intake record for verification."""
    try:
        with Session(engine) as session:
            intake = session.get(PatientIntake, intake_id)
            if not intake:
                return None

            # Decrypt the data
            data = intake.model_dump()
            data["name"] = decrypt_data(data["name"])
            data["contact"] = decrypt_data(data["contact"])

            return data
    except Exception as e:
        logger.error(f"Error retrieving intake: {e}")
        return None
