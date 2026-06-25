from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from livekit.agents import Agent, llm, JobContext
from prompts.persona import get_aarohi_instructions
from .database import save_intake
from .metrics import tool_calls

logger = logging.getLogger(__name__)

class AarohiTools:
    def __init__(self, job_ctx: JobContext, clinic_id: str):
        self.job_ctx = job_ctx
        self.clinic_id = clinic_id

    @llm.function_tool(description="Provides current date and time knowledge. Use this to tell the user the current date and time in a specific timezone. Defaults to UTC.")
    async def get_date_time(self, timezone: str = "UTC") -> str:
        """
        Retrieves the current date and time knowledge.
        :param timezone: The timezone to get the time for (e.g., 'UTC', 'Asia/Kolkata', 'America/New_York').
        """
        start = time.monotonic()
        try:
            now = datetime.now(ZoneInfo(timezone))
            result = now.strftime("%A, %B %d, %Y, %I:%M %p %Z")
            duration = time.monotonic() - start
            tool_calls.labels(tool_name="get_date_time", status="success").inc()
            logger.info("Tool get_date_time(%s) completed in %.3fs", timezone, duration)
            return result
        except Exception:
            now = datetime.now(ZoneInfo("UTC"))
            result = now.strftime("%A, %B %d, %Y, %I:%M %p %Z")
            duration = time.monotonic() - start
            tool_calls.labels(tool_name="get_date_time", status="error").inc()
            logger.warning("Tool get_date_time(%s) fell back to UTC after %.3fs", timezone, duration)
            return result

    @llm.function_tool(description="Updates the visual progress bar on the user's screen. Call this tool silently whenever you have successfully gathered new information from the patient.")
    async def update_progress_ui(self, completed_fields: list[str]) -> str:
        """
        Sends a progress update to the frontend UI.
        :param completed_fields: A list of strings representing the fields you have gathered so far. Valid options are EXACTLY: ["Name", "Age/Gender", "Contact", "Symptoms", "Duration/Severity", "History"]
        """
        start = time.monotonic()
        payload = json.dumps({
            "type": "progress_update",
            "completed": completed_fields
        })

        try:
            await self.job_ctx.room.local_participant.publish_data(
                payload=payload,
                topic="extraction_update"
            )
            duration = time.monotonic() - start
            tool_calls.labels(tool_name="update_progress_ui", status="success").inc()
            logger.info("Tool update_progress_ui(%s) completed in %.3fs", completed_fields, duration)
            return "SUCCESS: Progress UI updated."
        except Exception as e:
            duration = time.monotonic() - start
            tool_calls.labels(tool_name="update_progress_ui", status="error").inc()
            logger.error("Tool update_progress_ui failed after %.3fs: %s", duration, e)
            return "ERROR: Failed to update UI."

    @llm.function_tool(description="Submit the final patient intake report to the clinic database. Call this immediately after providing the verbal summary.")
    async def submit_intake_report(
        self,
        patient_name: str,
        chief_complaint: str,
        symptom_duration: str,
        severity_score: int,
        age: int = 0,
        gender: str = "Not specified",
        contact_number: str = "Not provided",
        medications: str = "None",
        known_conditions: str = "None"
    ) -> str:
        """
        Submits the collected patient data to the backend database.
        :param patient_name: Full name of the patient.
        :param chief_complaint: The main health concern.
        :param symptom_duration: How long the symptoms have lasted.
        :param severity_score: Pain or discomfort level strictly as an integer from 1 to 10.
        :param age: Age of the patient as an integer. Use 0 if unknown.
        :param gender: Gender of the patient.
        :param contact_number: Patient's phone or contact info.
        :param medications: Any current medications.
        :param known_conditions: Any existing medical conditions.
        """
        start = time.monotonic()
        logger.info("Tool submit_intake_report called for patient at clinic=%s", self.clinic_id)

        # Input validation with explicit type coercion
        try:
            severity_score = int(severity_score)
            age = int(age)
        except (ValueError, TypeError):
            return "ERROR: Severity and age must be whole numbers. Please ask the patient again."
        if severity_score < 1 or severity_score > 10:
            return "ERROR: Severity score must be between 1 and 10. Please ask the patient again."
        if age < 0 or age > 150:
            return "ERROR: Age must be between 0 and 150. Please verify with the patient."

        _max_field_len = 1000
        for _field_name, _field_val in (
            ("Patient name", patient_name),
            ("Chief complaint", chief_complaint),
            ("Symptom duration", symptom_duration),
            ("Gender", gender),
            ("Contact number", contact_number),
            ("Medications", medications),
            ("Known conditions", known_conditions),
        ):
            if len(_field_val) > _max_field_len:
                return f"ERROR: {_field_name} exceeds maximum length. Please provide a shorter value."

        conditions_str = known_conditions if known_conditions else "None"
        medications_str = medications if medications else "None"
        data = {
            "patient_name": patient_name,
            "age": str(age) if age > 0 else "Unknown",
            "gender": gender,
            "chief_complaint": chief_complaint,
            "symptom_duration": symptom_duration,
            "severity_score": f"{severity_score}/10",
            "current_medications": medications_str,
            "known_conditions": conditions_str,
        }
        
        success = save_intake({
            "name": patient_name,
            "age": age,
            "gender": gender,
            "contact": contact_number,
            "complaint": chief_complaint,
            "duration": symptom_duration,
            "severity": severity_score,
            "medications": medications,
            "conditions": known_conditions,
        }, clinic_id=self.clinic_id)

        if success:
            payload = json.dumps({
                "type": "intake_finished",
                "all_data": data,
                "message": "Intake successfully processed."
            })
            
            try:
                await self.job_ctx.room.local_participant.publish_data(
                    payload=payload,
                    topic="extraction_update"
                )
                logger.info("Intake completion signal sent to UI.")
            except Exception as e:
                logger.error("Intake signal publish failed: %s", e)

            duration = time.monotonic() - start
            tool_calls.labels(tool_name="submit_intake_report", status="success").inc()
            logger.info("Tool submit_intake_report succeeded in %.3fs", duration)
            return "SUCCESS: Intake saved. You can now deliver the final goodbye."
        else:
            duration = time.monotonic() - start
            tool_calls.labels(tool_name="submit_intake_report", status="error").inc()
            logger.error("Tool submit_intake_report failed after %.3fs", duration)
            return "ERROR: Database save failed. Try one more time."

class IntakeAgent(Agent):
    def __init__(self, job_ctx: JobContext) -> None:
        # Extract clinic_id from room name (formatted as clinicid_roomid)
        room_name = job_ctx.room.name
        if "_" in room_name:
            clinic_id = room_name.split("_")[0]
        else:
            logger.warning(
                "Room name '%s' has no underscore — cannot extract clinic_id",
                room_name,
            )
            clinic_id = "unknown"

        self._aarohi_tools = AarohiTools(job_ctx, clinic_id)
        super().__init__(
            instructions=get_aarohi_instructions(),
            tools=[
                self._aarohi_tools.get_date_time,
                self._aarohi_tools.submit_intake_report,
                self._aarohi_tools.update_progress_ui
            ]
        )

    def get_tool_list(self):
        return [
            self._aarohi_tools.get_date_time,
            self._aarohi_tools.submit_intake_report,
            self._aarohi_tools.update_progress_ui
        ]
