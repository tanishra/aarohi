import sqlite3
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Use an environment variable for the DB path, defaulting to a local file.
# On deployment, you would set DB_PATH to something like '/data/aarohi.db'
DB_PATH = os.getenv("DB_PATH", "aarohi_intake.db")

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patient_intake (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                age INTEGER,
                gender TEXT,
                contact TEXT,
                complaint TEXT,
                duration TEXT,
                severity INTEGER,
                medications TEXT,
                conditions TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
        logger.info(f"Local SQLite database initialized at {DB_PATH}")
    except Exception as e:
        logger.error(f"Error initializing local database: {e}")

def save_intake(data: dict):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO patient_intake 
            (name, age, gender, contact, complaint, duration, severity, medications, conditions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("name"),
            data.get("age"),
            data.get("gender"),
            data.get("contact"),
            data.get("complaint"),
            data.get("duration"),
            data.get("severity"),
            data.get("medications"),
            data.get("conditions")
        ))
        conn.commit()
        conn.close()
        logger.info(f"Intake report for {data.get('name')} saved to local SQLite.")
        return True
    except Exception as e:
        logger.error(f"Error saving to local SQLite: {e}")
        return False
