import os
import re
from datetime import datetime
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

import llm
import caldav_client

load_dotenv()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your AI Calendar Agent. Tell me what to schedule.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    # Get local time and simple ISO format for the LLM
    # E.g., '2026-02-28T11:20:00'
    now = datetime.now()
    current_time_iso = now.isoformat(timespec='seconds')
    
    await update.message.reply_text("Thinking...")

    try:
        existing_events = caldav_client.get_existing_events()
        parsed = llm.parse_event_intent(user_text, current_time_iso, existing_events)
        if not parsed or not parsed.get('is_valid'):
            await update.message.reply_text("I couldn't understand an event request from that.")
            return

        action = parsed.get('action')
        
        if action == "create":
            summary = parsed.get('summary')
            start_time_str = re.sub(r"Z|([+-]\d{2}:\d{2})$", "", parsed['start_time_iso'])
            end_time_str = re.sub(r"Z|([+-]\d{2}:\d{2})$", "", parsed['end_time_iso'])

            start_time = datetime.fromisoformat(start_time_str)
            end_time = datetime.fromisoformat(end_time_str)

            caldav_client.add_event(summary, start_time, end_time)
            
        elif action == "update":
            uid = parsed.get('uid')
            if not uid:
                await update.message.reply_text("I couldn't identify which event to update.")
                return
            
            new_summary = parsed.get('summary')
            new_start_str = parsed.get('start_time_iso')
            new_end_str = parsed.get('end_time_iso')
            
            new_start_time = datetime.fromisoformat(re.sub(r"Z|([+-]\d{2}:\d{2})$", "", new_start_str)) if new_start_str else None
            new_end_time = datetime.fromisoformat(re.sub(r"Z|([+-]\d{2}:\d{2})$", "", new_end_str)) if new_end_str else None
            
            caldav_client.update_event(uid, new_summary, new_start_time, new_end_time)

        elif action == "delete":
            uid = parsed.get('uid')
            if not uid:
                await update.message.reply_text("I couldn't identify which event to delete.")
                return
            
            caldav_client.delete_event(uid)
            
        else:
            await update.message.reply_text("I'm not sure what you want me to do with this event.")
            return

        bot_response = parsed.get('bot_response', "Alright, I've updated your calendar!")
        await update.message.reply_text(bot_response)
        
    except Exception as e:
        print(f"Error: {e}")
        if "GEMINI_QUOTA_REACHED" in str(e):
            await update.message.reply_text("I've reached my Gemini API free tier quota limit for now. Please wait a bit and try again later!")
        else:
            await update.message.reply_text(f"Sorry, an error occurred while scheduling your event: {e}")

def main():
    token = os.getenv("TELEGRAM_TOKEN")
    # Print to test if env is loaded
    print("Loading env variables...")
    print(os.getenv("TELEGRAM_TOKEN"))
    print(os.getenv("GEMINI_API_KEY"))

    if not token or token == "your_telegram_bot_token_here":
        print("Please configure your .env file with TELEGRAM_TOKEN and GEMINI_API_KEY.")
        return
        
    app = ApplicationBuilder().token(token).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("AI Calendar Bot polling for messages...")
    app.run_polling()

if __name__ == '__main__':
    main()
