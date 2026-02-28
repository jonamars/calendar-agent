# AI Calendar Manager

AI Calendar Manager is a powerful, locally hosted Google AI-driven Telegram bot
that manages a Radicale CalDAV server. Simply chat with your bot in natural
language, and it handles creating, updating, and deleting events on your
personal calendar flawlessly.

## Features

- **Natural Language Parsing**: Just text "Schedule a meeting with Jona for
  tomorrow at 3 PM". No clunky calendar interfaces required.
- **Context-Aware Modifying**: The AI understands your existing events! Text
  "Move my meeting with Jona to 5 PM" or "Cancel my 3 PM meeting", and the bot
  will accurately modify or delete the corresponding event.
- **CalDAV Synchronization**: Includes a fully functional Radicale CalDAV
  server. Connect your native Apple Calendar, GNOME Calendar, Thunderbird, or
  Android client to passively view all your AI-scheduled events from any device.
- **Dockerized**: Fully orchestrated using Docker Compose for a true one-command
  spin up.
- **Blisteringly Fast**: The Python environment is built and solved
  automatically inside the container using the exceptional `uv` package manager
  (`ghcr.io/astral-sh/uv`).

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and
  [Docker Compose](https://docs.docker.com/compose/install/)
- A Telegram Bot Token from [@BotFather](https://t.me/botfather)
- A [Google AI API Key](https://aistudio.google.com/app/apikey)

## Quick Start Setup

**1. Clone the repository**

```bash
git clone https://github.com/jonamars/calendar-agent.git
cd calendar-agent
```

**2. Configure Environment Variables**

Copy the example configuration file:

```bash
cp env.example .env
```

Open `.env` and paste your genuine `TELEGRAM_TOKEN` and `GOOGLE_API_KEY`.

```bash
cp radicale/users.example users
```

Update to the username/password of your choosing.

**3. Launch!**

Run the stack in the background:

```bash
docker compose up -d --build
```

This single command spins up the Radicale CalDAV server on `:5232` and launches
the python Telegram listener in parallel!

## Usage

### Using the AI Agent

Open Telegram, navigate to the bot you created, and say `Hello`! You can type
anything like:

- "Add lunch with Alice tomorrow at 1 PM"
- "Change my lunch with Alice to 2 PM"
- "Cancel my lunch with Alice"
- "I have a dentist appointment next Tuesday at 9am for 45 minutes"

### Viewing your Calendar on other Devices

Because the application runs standard Radicale, you can seamlessly add it to
your Calendar apps.

1. Open your Calendar settings (e.g. Apple Calendar on iPhone/Mac, or GNOME
   Calendar on Linux).
2. Add a new **CalDAV** account.
3. Use the following credentials:
   - **URL:** `http://<your-machine-ip>:5232/<username>/` _(or localhost if on
     the same machine)_
   - **Username:** `<username>`
   - **Password:** `<password>`

Any event you ask the bot to create will push immediately to your native device.
