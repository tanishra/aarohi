from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class SessionContext:
    session_id: str = field(default_factory=lambda: str(uuid4()))
    session_token: str = field(default_factory=lambda: str(uuid4()))
    hospital_id: str | None = None

    current_state: str = "active"
    turn_number: int = 0
    language: str = "en"
    retry_count: int = 0
    correction_count: int = 0

    patient_name: str | None = None
    age: int | None = None
    age_approximate: bool = False
    gender: str | None = None
    contact_number: str | None = None
    chief_complaint: str | None = None
    symptom_duration: str | None = None
    severity_score: int | None = None
    known_conditions: list[str] = field(default_factory=list)
    current_medications: list[str] = field(default_factory=list)

    emergency_flag: bool = False
    confirmed: bool = False
    session_ended_by: str = ""
    correction_target: str | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: datetime | None = None

    def increment_turn(self) -> None:
        self.turn_number += 1

    def mark_emergency(self) -> None:
        self.emergency_flag = True
        self.current_state = "emergency"

    def mark_ended(self, ended_by: str) -> None:
        self.session_ended_by = ended_by
        self.ended_at = datetime.now(timezone.utc)

    def collected_summary(self) -> str:
        sections = [
            f"Name: {self.patient_name or 'Not provided'}",
            f"Age: {self.age if self.age is not None else 'Not provided'}",
            f"Gender: {self.gender or 'Not provided'}",
            f"Chief complaint: {self.chief_complaint or 'Not provided'}",
            f"Symptom duration: {self.symptom_duration or 'Not provided'}",
            f"Severity: {self.severity_score if self.severity_score is not None else 'Not provided'}",
            "Known conditions: "
            + (", ".join(self.known_conditions) if self.known_conditions else "Not provided"),
            "Current medications: "
            + (
                ", ".join(self.current_medications)
                if self.current_medications
                else "Not provided"
            ),
        ]
        return "\n".join(sections)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["started_at"] = self.started_at.isoformat()
        data["ended_at"] = self.ended_at.isoformat() if self.ended_at else None
        return data
