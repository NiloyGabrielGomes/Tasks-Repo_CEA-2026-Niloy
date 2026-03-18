import os
from functools import lru_cache
from pydantic import BaseModel


class Settings(BaseModel):
    # Discord
    DISCORD_PUBLIC_KEY: str = ""
    DISCORD_APPLICATION_ID: str = ""
    DISCORD_BOT_TOKEN: str = ""
    DISCORD_GUILD_ID: str = ""
    DISCORD_CLIENT_ID: str = ""
    DISCORD_CLIENT_SECRET: str = ""
    DISCORD_REDIRECT_URI: str = ""

    # Role mapping: Discord role name -> Application role
    ROLE_ADMIN: str = "MHP-Admin"
    ROLE_TEAM_LEAD: str = "MHP-TeamLead"
    ROLE_EMPLOYEE: str = "MHP-Employee"

    # Role IDs (optional - for faster lookups)
    ROLE_ADMIN_ID: str = ""
    ROLE_TEAM_LEAD_ID: str = ""

    DYNAMODB_TABLE_NAME: str = "MHP-Data"

    S3_BUCKET: str = "mhp-reports"
    S3_PREFIX: str = "reports/"

    CUTOFF_TIME: str = "21:00"  # HH:MM in Asia/Dhaka (UTC+6)
    WFH_MONTHLY_CAP: int = 5
    FORWARD_PLANNING_DAYS: int = 7

    # Timezone
    TIMEZONE: str = "Asia/Dhaka"
    
    # Debug mode
    DEBUG: bool = False

    # Multi-Lambda dispatch
    ENABLE_MULTI_LAMBDA: bool = False
    MEAL_FUNCTION_NAME: str = ""
    LOCATION_FUNCTION_NAME: str = ""
    OVERRIDE_FUNCTION_NAME: str = ""

@lru_cache()
def get_settings() -> Settings:
    return Settings(
        DISCORD_PUBLIC_KEY=os.getenv("DISCORD_PUBLIC_KEY", ""),
        DISCORD_APPLICATION_ID=os.getenv("DISCORD_APPLICATION_ID", ""),
        DISCORD_BOT_TOKEN=os.getenv("DISCORD_BOT_TOKEN", ""),
        DISCORD_GUILD_ID=os.getenv("DISCORD_GUILD_ID", ""),
        DISCORD_CLIENT_ID=os.getenv("DISCORD_CLIENT_ID", ""),
        DISCORD_CLIENT_SECRET=os.getenv("DISCORD_CLIENT_SECRET", ""),
        DISCORD_REDIRECT_URI=os.getenv("DISCORD_REDIRECT_URI", ""),
        ROLE_ADMIN=os.getenv("ROLE_ADMIN", "MHP-Admin"),
        ROLE_TEAM_LEAD=os.getenv("ROLE_TEAM_LEAD", "MHP-TeamLead"),
        ROLE_EMPLOYEE=os.getenv("ROLE_EMPLOYEE", "MHP-Employee"),
        ROLE_ADMIN_ID=os.getenv("ROLE_ADMIN_ID", ""),
        ROLE_TEAM_LEAD_ID=os.getenv("ROLE_TEAM_LEAD_ID", ""),
        DYNAMODB_TABLE_NAME=os.getenv("DYNAMODB_TABLE_NAME", "MHP-Data"),
        S3_BUCKET=os.getenv("S3_BUCKET", "mhp-reports"),
        S3_PREFIX=os.getenv("S3_PREFIX", "reports/"),
        CUTOFF_TIME=os.getenv("CUTOFF_TIME", "21:00"),
        WFH_MONTHLY_CAP=int(os.getenv("WFH_MONTHLY_CAP", "5")),
        FORWARD_PLANNING_DAYS=int(os.getenv("FORWARD_PLANNING_DAYS", "7")),
        TIMEZONE=os.getenv("TIMEZONE", "Asia/Dhaka"),
        DEBUG=os.getenv("DEBUG", "false").lower() == "true",
        ENABLE_MULTI_LAMBDA=os.getenv("ENABLE_MULTI_LAMBDA", "false").lower() == "true",
        MEAL_FUNCTION_NAME=os.getenv("MEAL_FUNCTION_NAME", ""),
        LOCATION_FUNCTION_NAME=os.getenv("LOCATION_FUNCTION_NAME", ""),
        OVERRIDE_FUNCTION_NAME=os.getenv("OVERRIDE_FUNCTION_NAME", ""),
    )
settings = get_settings()
