import os
import json
import traceback
from typing import Literal, Optional
from google import genai
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL = "gemma-3-27b-it"

class EventDetails(BaseModel):
    action: Literal["create", "update", "delete"] = Field(description="The action the user wants to take.")
    summary: Optional[str] = Field(None, description="The title or summary of the event.")
    start_time_iso: Optional[str] = Field(None, description="The start time in strict ISO 8601 without timezone attached (e.g., '2026-02-28T14:00:00')")
    end_time_iso: Optional[str] = Field(None, description="The end time in strict ISO 8601 without timezone attached (e.g., '2026-02-28T15:00:00'). Assume 1h default.")
    uid: Optional[str] = Field(None, description="If updating or deleting, the exact UID of the event to modify from the provided context.")
    bot_response: str = Field(description="A friendly, conversational confirmation message to send back to the user on Telegram detailing the action.")
    calendar: Optional[str] = Field(None, description="The name of the calendar to categorize the event into (e.g., 'Work', 'Personal').")
    is_valid: bool = Field(description="True if an event intent can be parsed, False if not.")

def parse_event_intent(user_text: str, current_time_iso: str, existing_events: list = []) -> dict:
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not found.")
        
    client = genai.Client(api_key=GOOGLE_API_KEY)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(base_dir, "prompts", "event_parsing.txt")
    print(prompt_path)
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    prompt = prompt_template.format(
        current_time_iso=current_time_iso,
        existing_events=json.dumps(existing_events, indent=2)
    )
    
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=f"{prompt}\nUser request: {user_text}",
        )
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        print(f"Raw LLM Response:\n{text}")
        
        parsed_data = json.loads(text)
        # Ensure it fits the Pydantic model by passing it through (optional but safe)
        event_details = EventDetails(**parsed_data)
        return event_details.model_dump()
    except Exception as e:
        print(f"Error calling AI API: {e}")
        traceback.print_exc()
        error_str = str(e).lower()
        if "429" in error_str and "quota" in error_str:
            raise Exception("AI_QUOTA_REACHED") from e
        return None
