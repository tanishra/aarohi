from __future__ import annotations

import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from livekit.agents import Agent, llm, JobContext
from prompts.persona import get_aarohi_instructions
from .database import save_intake

logger = logging.getLogger(__name__)

class AarohiTools:
    def __init__(self, job_ctx: JobContext):
        self.job_ctx = job_ctx

    @llm.function_tool(description="Provides current date and time knowledge. Use this to tell the user the current date and time in a specific timezone. Defaults to UTC.")
    async def get_date_time(self, timezone: str = "UTC") -> str:
        """
        Retrieves the current date and time knowledge.
        :param timezone: The timezone to get the time for (e.g., 'UTC', 'Asia/Kolkata', 'America/New_York').
        """
        try:
            now = datetime.now(ZoneInfo(timezone))
            return now.strftime("%A, %B %d, %Y, %I:%M %p %Z")
        except Exception:
            now = datetime.now(ZoneInfo("UTC"))
            return now.strftime("%A, %B %d, %Y, %I:%M %p %Z")

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
        logger.info(f"Finalizing intake for: {patient_name}")
        
        data = {
            "patient_name": patient_name,
            "age": str(age) if age > 0 else "Unknown",
            "gender": gender,
            "contact_number": contact_number,
            "chief_complaint": chief_complaint,
            "symptom_duration": symptom_duration,
            "severity_score": f"{severity_score}/10",
            "current_medications": medications,
            "known_conditions": known_conditions
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
            "conditions": known_conditions
        })

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
                logger.error(f"Signal failed: {e}")

            return "SUCCESS: Intake saved. You can now deliver the final goodbye."
        else:
            return "ERROR: Database save failed. Try one more time."

class IntakeAgent(Agent):
    def __init__(self, job_ctx: JobContext) -> None:
        self._aarohi_tools = AarohiTools(job_ctx)
        super().__init__(
            instructions=get_aarohi_instructions(),
            tools=[
                self._aarohi_tools.get_date_time,
                self._aarohi_tools.submit_intake_report
            ]
        )

    def get_tool_list(self):
        return [
            self._aarohi_tools.get_date_time,
            self._aarohi_tools.submit_intake_report
        ]
