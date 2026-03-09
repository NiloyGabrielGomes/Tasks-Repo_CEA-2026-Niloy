"""
Register Discord slash commands for the MHP bot.

Usage:
    1. Copy .env.example to .env and fill in your Discord credentials
    2. Run: python scripts/register_commands.py

This registers guild-scoped commands (instant availability).
Run once after initial setup, or whenever command definitions change.
"""

import os
import sys
import json

import httpx
from dotenv import load_dotenv

# Load .env from backend/ root
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(env_path)

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
DISCORD_APPLICATION_ID = os.getenv("DISCORD_APPLICATION_ID", "") or os.getenv("DISCORD_CLIENT_ID", "")
DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD_ID", "")

DISCORD_API_BASE = "https://discord.com/api/v10"

# ── Command Definitions ─────────────────────────────────────────────────────

COMMANDS = [
    {
        "name": "meal-update",
        "type": 1,  # CHAT_INPUT
        "description": "View and toggle your meal participation for a date",
        "options": [
            {
                "name": "date",
                "description": "Date in YYYY-MM-DD format (defaults to today)",
                "type": 3,  # STRING
                "required": False,
            }
        ],
    },
    {
        "name": "work-location",
        "type": 1,
        "description": "View and set your work location (Office/WFH) for a date",
        "options": [
            {
                "name": "date",
                "description": "Date in YYYY-MM-DD format (defaults to today)",
                "type": 3,
                "required": False,
            }
        ],
    },
]


def validate_config():
    missing = []
    if not DISCORD_BOT_TOKEN:
        missing.append("DISCORD_BOT_TOKEN")
    if not DISCORD_APPLICATION_ID:
        missing.append("DISCORD_APPLICATION_ID (or DISCORD_CLIENT_ID)")
    if not DISCORD_GUILD_ID:
        missing.append("DISCORD_GUILD_ID")

    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        print("Copy .env.example to .env and fill in your Discord credentials.")
        sys.exit(1)


def register_guild_commands():
    """Register commands scoped to a specific guild (instant availability)."""
    url = f"{DISCORD_API_BASE}/applications/{DISCORD_APPLICATION_ID}/guilds/{DISCORD_GUILD_ID}/commands"

    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json",
    }

    print(f"Registering {len(COMMANDS)} commands to guild {DISCORD_GUILD_ID}...")
    print(f"Application ID: {DISCORD_APPLICATION_ID}")
    print()

    # PUT overwrites all guild commands atomically
    response = httpx.put(url, headers=headers, json=COMMANDS, timeout=30)

    if response.status_code == 200:
        registered = response.json()
        print(f"Successfully registered {len(registered)} commands:")
        for cmd in registered:
            options_str = ""
            if cmd.get("options"):
                opts = [f"[{o['name']}]" for o in cmd["options"]]
                options_str = " " + " ".join(opts)
            print(f"  /{cmd['name']}{options_str} (id: {cmd['id']})")
        print()
        print("Commands are available immediately in the guild.")
    else:
        print(f"ERROR: {response.status_code}")
        print(response.text)
        sys.exit(1)


def list_guild_commands():
    """List currently registered guild commands."""
    url = f"{DISCORD_API_BASE}/applications/{DISCORD_APPLICATION_ID}/guilds/{DISCORD_GUILD_ID}/commands"
    headers = {"Authorization": f"Bot {DISCORD_BOT_TOKEN}"}

    response = httpx.get(url, headers=headers, timeout=30)

    if response.status_code == 200:
        commands = response.json()
        if not commands:
            print("No commands registered.")
            return
        print(f"Currently registered commands ({len(commands)}):")
        for cmd in commands:
            print(f"  /{cmd['name']} — {cmd.get('description', '(no description)')}")
    else:
        print(f"ERROR: {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    validate_config()

    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        list_guild_commands()
    else:
        register_guild_commands()
