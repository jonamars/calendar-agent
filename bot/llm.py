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
    is_valid: bool = Field(description="True if an event intent can be parsed, False if not.")

def parse_event_intent(user_text: str, current_time_iso: str, existing_events: list = []) -> dict:
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not found.")
        
    client = genai.Client(api_key=GOOGLE_API_KEY)
    
    prompt = f"""
You are an AI calendar assistant capable of creating, updating, and deleting events.

# CONTEXT
Current local time: {current_time_iso} (Assume all user times are in this local timezone)
Existing calendar events:
{json.dumps(existing_events, indent=2)}

# INSTRUCTIONS
1. Analyze the user request to determine the intended action: "create", "update", or "delete".
2. For "create": Provide a summary, start_time_iso, and end_time_iso. If no time is provided, use a time that is reasonable for the type of event.
3. For "update": Provide the EXACT `uid` of the event to modify from the existing events above. Provide the NEW summary, start_time_iso, and end_time_iso. Retain original values for any fields the user does not wish to change.
4. For "delete": Provide the EXACT `uid` of the event to delete.
5. Format the `summary` nicely: Use strict Title Case (capitalize all major words, rest lowercase (e.g. lowercase 'with' and 'the')). Include ONLY what the event is, excluding any temporal or temporal-relative words (omit "tomorrow", "at 4pm", "on Tuesday", etc.). Append a single relevant emoji at the end (e.g., "Lunch with Alice 🍱").

# OUTPUT FORMAT
Return a raw, unmarkdown-wrapped JSON object strictly adhering to this schema. DO NOT output ```json codeblocks.
{{
  "action": "create" | "update" | "delete",
  "summary": "String (formatted event title without time references, with emoji)",
  "start_time_iso": "String (ISO 8601 format, e.g., '2026-02-28T14:00:00')",
  "end_time_iso": "String (ISO 8601 format, e.g., '2026-02-28T15:00:00')",
  "uid": "String (Target event UID, only for update or delete)",
  "bot_response": "String (A friendly, conversational confirmation message to the user detailing your action. ALWAYS use European 24-hour formatting for any times mentioned, e.g., '14:00' instead of '2 PM'). Also european ordered dates.",
  "is_valid": true | false (True if you successfully parsed the calendar intent, false otherwise)
}}
"""
    
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
