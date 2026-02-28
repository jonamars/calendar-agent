import os
import json
import traceback
from google import genai
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class EventDetails(BaseModel):
    summary: str = Field(description="The title or summary of the event.")
    start_time_iso: str = Field(description="The start time in strict ISO 8601 without timezone attached (e.g., '2026-02-28T14:00:00')")
    end_time_iso: str = Field(description="The end time in strict ISO 8601 without timezone attached (e.g., '2026-02-28T15:00:00'). Assume 1h default.")
    is_valid: bool = Field(description="True if an event can be parsed, False if not.")

def parse_event_intent(user_text: str, current_time_iso: str) -> dict:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found.")
        
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
You are an AI calendar assistant. Extract event details from the user's text.
The current local time is: {current_time_iso}.
All provided times will be assumed to be in the user's local timezone.
Return the result strictly as JSON formatted with Double Quotes. Make sure the output fits the Pydantic schema structure logic.
"""
    
    try:
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
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
