import os

import pytest
from sqlmodel import Session, text

from core.database import (
    LOCAL_DB_PATH,
    engine_local,
    engine_cloud,
    init_db,
    save_intake,
    get_intake,
    sync_local_to_cloud,
    PatientIntake,
)


@pytest.fixture(autouse=True)
def clean_db():
    from sqlmodel import SQLModel
    SQLModel.metadata.drop_all(engine_local)
    init_db()
    yield


def test_init_db_creates_tables():
    init_db()
    with Session(engine_local) as session:
        result = session.exec(text(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )).all()
        table_names = [r[0] for r in result]
    assert "patientintake" in table_names
    assert "clinic" in table_names


def test_save_intake_to_local():
    init_db()
    result = save_intake(
        data={
            "name": "Test Patient",
            "age": 30,
            "gender": "Male",
            "contact": "9999999999",
            "complaint": "Headache",
            "duration": "3 days",
            "severity": 5,
            "medications": "None",
            "conditions": "None",
        },
        clinic_id="test-clinic",
    )
    assert result is True


def test_get_intake_after_save():
    init_db()
    save_intake(
        data={
            "name": "Jane Doe",
            "age": 25,
            "gender": "Female",
            "contact": "8888888888",
            "complaint": "Fever",
            "duration": "2 days",
            "severity": 6,
            "medications": "Paracetamol",
            "conditions": "None",
        },
        clinic_id="test-clinic",
    )
    record = get_intake(intake_id=1, from_local=True)
    assert record is not None
    assert record["name"] == "Jane Doe"
    assert record["age"] == 25
    assert record["severity"] == 6
    assert record["complaint"] == "Fever"


def test_get_intake_not_found():
    result = get_intake(intake_id=99999, from_local=True)
    assert result is None


def test_save_intake_no_cloud_fallback():
    assert engine_cloud is None
    result = save_intake(
        data={
            "name": "No Cloud",
            "age": 40,
            "gender": "Female",
            "contact": "7777777777",
            "complaint": "Cough",
            "duration": "1 week",
            "severity": 4,
            "medications": "None",
            "conditions": "Asthma",
        },
        clinic_id="test-clinic",
    )
    assert result is True


def test_pii_encrypted_at_rest():
    init_db()
    save_intake(
        data={
            "name": "Secret Patient",
            "age": 35,
            "gender": "Male",
            "contact": "6666666666",
            "complaint": "Pain",
            "duration": "1 day",
            "severity": 3,
            "medications": "None",
            "conditions": "None",
        },
        clinic_id="test-clinic",
    )
    with Session(engine_local) as session:
        raw = session.get(PatientIntake, 1)
        assert raw is not None
        assert raw.name != "Secret Patient"
        assert raw.contact != "6666666666"

    record = get_intake(intake_id=1, from_local=True)
    assert record is not None
    assert record["name"] == "Secret Patient"


def test_sync_local_to_cloud_no_cloud_engine():
    result = sync_local_to_cloud()
    assert result is None


def test_multiple_intakes():
    init_db()
    for i in range(3):
        save_intake(
            data={
                "name": f"Patient {i}",
                "age": 20 + i,
                "gender": "Female",
                "contact": f"111111{i}",
                "complaint": "Checkup",
                "duration": "N/A",
                "severity": 1,
                "medications": "None",
                "conditions": "None",
            },
            clinic_id="test-clinic",
        )
    for i in range(1, 4):
        record = get_intake(intake_id=i, from_local=True)
        assert record is not None
        assert record["name"] == f"Patient {i - 1}"
