import os
import json
import traceback
from typing import Literal, Optional
from google import genai
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = "gemini-2.5-flash"

class EventDetails(BaseModel):
    action: Literal["create", "update", "delete"] = Field(description="The action the user wants to take.")
    summary: Optional[str] = Field(None, description="The title or summary of the event.")
    start_time_iso: Optional[str] = Field(None, description="The start time in strict ISO 8601 without timezone attached (e.g., '2026-02-28T14:00:00')")
    end_time_iso: Optional[str] = Field(None, description="The end time in strict ISO 8601 without timezone attached (e.g., '2026-02-28T15:00:00'). Assume 1h default.")
    uid: Optional[str] = Field(None, description="If updating or deleting, the exact UID of the event to modify from the provided context.")
    bot_response: str = Field(description="A friendly, conversational confirmation message to send back to the user on Telegram detailing the action.")
    is_valid: bool = Field(description="True if an event intent can be parsed, False if not.")

def parse_event_intent(user_text: str, current_time_iso: str, existing_events: list = []) -> dict:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found.")
        
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
You are an AI calendar assistant. Extract event details from the user's text.
The user might want to CREATE, UPDATE, or DELETE an event.
The current local time is: {current_time_iso}.
All provided times will be assumed to be in the user's local timezone.

Here are the user's existing calendar events mapped by UID:
{json.dumps(existing_events, indent=2)}

If the user wants to create an event, provide summary, start_time_iso, and end_time_iso.
If the user wants to update an event, you MUST provide the EXACT 'uid' from the existing events above that corresponds to their request. ALSO provide the NEW summary, start_time_iso, and end_time_iso corresponding to the modifications. Retain the original start/end times if the user only specifies a name change, or retain the original name if the user only specifies a time change.
If the user wants to delete an event, you MUST provide the EXACT 'uid' from the existing events above.

Return the result strictly as JSON. Make sure the output fits the Pydantic schema structure logic.
"""
    
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=f"{prompt}\nUser request: {user_text}",
            config={
                'response_mime_type': 'application/json',
                'response_schema': EventDetails,
            },
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        traceback.print_exc()
        return None
