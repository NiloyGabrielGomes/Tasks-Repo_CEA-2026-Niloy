"""
Seed DynamoDB with initial data for the MHP bot.

Usage:
    python scripts/seed_data.py

Seeds:
  - team_role_map policy (maps Discord role IDs → team names)
  - Test users (optional, for development)
"""

import os
import sys
import json
from datetime import datetime

import boto3
from dotenv import load_dotenv

# Load .env from backend/ root
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(env_path)

TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "trainee-2026-niloy-mhp-data")
REGION = os.getenv("AWS_REGION", "ap-south-1")


def get_table():
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    return dynamodb.Table(TABLE_NAME)


def seed_team_role_map(table):
    """
    Seed the team_role_map policy.
    Maps Discord role IDs to team names.
    Update the role IDs below with your actual Discord role IDs.
    """
    # TODO: Replace these placeholder role IDs with your actual Discord role IDs
    team_role_map = {
        # "DISCORD_ROLE_ID": "Team Name"
        # Example:
        # "1234567890123456789": "Backend",
        # "9876543210987654321": "Frontend",
    }

    now = datetime.utcnow().isoformat()

    table.put_item(Item={
        "PK": "POLICY#team_role_map",
        "SK": "-",
        "name": "team_role_map",
        "value": json.dumps(team_role_map),
        "updated_at": now,
    })

    print(f"Seeded team_role_map policy with {len(team_role_map)} mappings")


def seed_default_policies(table):
    """Seed default policy values."""
    now = datetime.utcnow().isoformat()

    policies = [
        ("cutoff_time", "21:00"),
        ("wfh_monthly_cap", "5"),
        ("forward_planning_days", "7"),
    ]

    for name, value in policies:
        table.put_item(Item={
            "PK": f"POLICY#{name}",
            "SK": "-",
            "name": name,
            "value": value,
            "updated_at": now,
        })

    print(f"Seeded {len(policies)} default policies")


def seed_test_user(table, discord_id: str, name: str, role: str = "employee", team: str = None):
    """Seed a test user."""
    now = datetime.utcnow().isoformat()

    item = {
        "PK": f"USER#{discord_id}",
        "SK": "PROFILE",
        "discord_id": discord_id,
        "name": name,
        "role": role,
        "is_active": True,
        "created_at": now,
    }
    if team:
        item["team"] = team

    table.put_item(Item=item)
    print(f"  Seeded user: {name} ({discord_id}) — role={role}, team={team}")


if __name__ == "__main__":
    print(f"Table: {TABLE_NAME}")
    print(f"Region: {REGION}")
    print()

    table = get_table()

    # Seed policies
    seed_team_role_map(table)
    seed_default_policies(table)
    print()

    # Optionally seed test users (uncomment and update IDs)
    # print("Seeding test users:")
    # seed_test_user(table, "111111111111111111", "Test Admin", role="admin")
    # seed_test_user(table, "222222222222222222", "Test Lead", role="team_lead", team="Backend")
    # seed_test_user(table, "333333333333333333", "Test Employee", role="employee", team="Backend")

    print("Done!")
