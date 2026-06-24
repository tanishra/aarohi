import logging
import os
import time
from typing import Optional
from sqlmodel import Field, Session, SQLModel, create_engine, select
from .encryption import encrypt_data, decrypt_data

logger = logging.getLogger(__name__)

# --- Configuration ---
# Local Fallback Database
LOCAL_DB_PATH = os.getenv("LOCAL_DB_PATH", "aarohi_fallback.db")
sqlite_url = f"sqlite:///{LOCAL_DB_PATH}"
engine_local = create_engine(
    sqlite_url,
    echo=False,
    connect_args={"check_same_thread": False, "timeout": 15},
)

def _exec_with_retry(fn, max_retries=3, base_delay=0.5):
    last_error = None
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as e:
            last_error = e
            if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                time.sleep(base_delay * (2 ** attempt))
                continue
            raise
    raise last_error  # pragma: no cover

# Cloud Database (PostgreSQL, MySQL, etc.)
CLOUD_DB_URL = os.getenv("CLOUD_DB_URL")
engine_cloud = None
if CLOUD_DB_URL:
    try:
        # Use a short pool timeout so it fails fast and falls back
        engine_cloud = create_engine(CLOUD_DB_URL, echo=False, pool_timeout=5)
    except Exception as e:
        logger.error(f"Failed to initialize cloud engine. Will use local fallback. Error: {e}")

# --- Models ---
class Clinic(SQLModel, table=True):
    id: str = Field(primary_key=True, description="The unique username or ID of the clinic")
    hashed_password: str

class PatientIntake(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    clinic_id: str = Field(foreign_key="clinic.id")
    name: str
    age: int
    gender: str
    contact: str
    complaint: str
    duration: str
    severity: int
    medications: str
    conditions: str
    sync_status: str = Field(default="synced") # "synced" or "pending"

def init_db():
    """Initializes tables in both local and cloud databases."""
    start = time.monotonic()
    try:
        SQLModel.metadata.create_all(engine_local)
        logger.info("Local fallback database initialized at %s (%.3fs)", LOCAL_DB_PATH, time.monotonic() - start)
    except Exception as e:
        logger.error("Error initializing local database: %s", e)

    if engine_cloud:
        try:
            SQLModel.metadata.create_all(engine_cloud)
            logger.info("Cloud database initialized successfully.")
        except Exception as e:
            logger.warning("Could not initialize cloud database tables (might be unreachable): %s", e)

def save_intake(data: dict, clinic_id: str = "admin") -> bool:
    """Saves intake data for a specific clinic. Tries cloud first, falls back to local."""
    start = time.monotonic()
    try:
        # Encrypt PII
        encrypted_data = data.copy()
        for pii_field in ("name", "contact", "complaint", "medications", "conditions"):
            if pii_field in encrypted_data and encrypted_data[pii_field]:
                encrypted_data[pii_field] = encrypt_data(str(encrypted_data[pii_field]))

        # Inject clinic_id
        encrypted_data["clinic_id"] = clinic_id

        # Try Cloud DB First
        if engine_cloud:
            try:
                intake = PatientIntake(**encrypted_data, sync_status="synced")
                with Session(engine_cloud) as session:
                    session.add(intake)
                    session.commit()
                elapsed = time.monotonic() - start
                logger.info("Intake saved to CLOUD database for clinic %s (%.3fs)", clinic_id, elapsed)
                return True
            except Exception as e:
                logger.warning("Cloud DB failed, falling back to local: %s", e)

        # Fallback to Local DB with retry for SQLite contention
        def _save_local():
            intake = PatientIntake(**encrypted_data, sync_status="pending")
            with Session(engine_local) as session:
                session.add(intake)
                session.commit()
        _exec_with_retry(_save_local)
        elapsed = time.monotonic() - start
        logger.info("Intake saved to LOCAL fallback (pending) for clinic %s (%.3fs)", clinic_id, elapsed)
        return True

    except Exception as e:
        elapsed = time.monotonic() - start
        logger.error("FATAL: intake save failed for clinic %s after %.3fs: %s", clinic_id, elapsed, e)
        return False

def get_intake(intake_id: int, from_local: bool = False) -> Optional[dict]:
    """Helper method to retrieve and decrypt an intake record for verification."""
    engine_to_use = engine_local if from_local else (engine_cloud or engine_local)
    start = time.monotonic()

    try:
        with Session(engine_to_use) as session:
            intake = session.get(PatientIntake, intake_id)
            if not intake:
                return None

            data = intake.model_dump()
            data["name"] = decrypt_data(data["name"]) or ""
            data["contact"] = decrypt_data(data["contact"]) or ""
            data["complaint"] = decrypt_data(data["complaint"]) or ""
            data["medications"] = decrypt_data(data["medications"]) or ""
            data["conditions"] = decrypt_data(data["conditions"]) or ""
            elapsed = time.monotonic() - start
            logger.info("Intake %d retrieved in %.3fs", intake_id, elapsed)
            return data
    except Exception as e:
        elapsed = time.monotonic() - start
        logger.error("Error retrieving intake %d after %.3fs: %s", intake_id, elapsed, e)
        return None

def sync_local_to_cloud():
    """Background task to push pending local records to the cloud."""
    if not engine_cloud:
        logger.debug("No CLOUD_DB_URL configured. Skipping sync.")
        return

    start = time.monotonic()
    try:
        # Use expire_on_commit=False so record objects stay usable after commit
        with Session(engine_local, expire_on_commit=False) as session_local:
            # Find all pending records
            statement = select(PatientIntake).where(PatientIntake.sync_status == "pending")
            pending_records = session_local.exec(statement).all()

            if not pending_records:
                return

            logger.info("Found %d pending records. Starting sync to cloud...", len(pending_records))

            with Session(engine_cloud) as session_cloud:
                synced_count = 0
                for record in pending_records:
                    local_committed = False
                    try:
                        # Mark local as synced FIRST — prevents duplication on crash
                        _exec_with_retry(lambda: _mark_synced(session_local, record))
                        local_committed = True

                        # Now write to cloud
                        cloud_record_data = record.model_dump(exclude={"id"})
                        cloud_intake = PatientIntake(**cloud_record_data)
                        session_cloud.add(cloud_intake)
                        session_cloud.commit()

                        # Delete local record (best-effort cleanup, not correctness-critical)
                        session_local.delete(record)
                        session_local.commit()
                        synced_count += 1
                    except Exception as record_err:
                        session_cloud.rollback()
                        if local_committed:
                            # Revert local status to pending so it can be retried
                            try:
                                _exec_with_retry(lambda: _mark_pending(session_local, record))
                            except Exception:
                                session_local.rollback()
                        else:
                            session_local.rollback()
                        logger.error("Failed to sync record ID %d: %s", record.id, record_err)

                if synced_count > 0:
                    elapsed = time.monotonic() - start
                    logger.info("Synced %d records to cloud in %.3fs", synced_count, elapsed)

    except Exception as e:
        elapsed = time.monotonic() - start
        logger.error("Sync process failed after %.3fs: %s", elapsed, e)


def _mark_synced(session_local: Session, record: PatientIntake) -> None:
    record.sync_status = "synced"
    session_local.commit()

def _mark_pending(session_local: Session, record: PatientIntake) -> None:
    record.sync_status = "pending"
    session_local.commit()
