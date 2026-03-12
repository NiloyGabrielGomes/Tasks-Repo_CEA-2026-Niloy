import os
from functools import lru_cache
from pydantic import BaseModel


class Settings(BaseModel):
    # Discord
    DISCORD_PUBLIC_KEY: str = ""
    DISCORD_APPLICATION_ID: str = ""
    DISCORD_BOT_TOKEN: str = ""
    DISCORD_GUILD_ID: str = ""

    ROLE_ADMIN: str = "MHP-Admin"
    ROLE_TEAM_LEAD: str = "MHP-TeamLead"

    DYNAMODB_TABLE_NAME: str = "MHP-Data"

    S3_BUCKET: str = "mhp-reports"
    S3_PREFIX: str = "reports/"

    CUTOFF_TIME: str = "21:00"  # HH:MM in Asia/Dhaka (UTC+6)
    WFH_MONTHLY_CAP: int = 5
    FORWARD_PLANNING_DAYS: int = 7

    # Timezone
    TIMEZONE: str = "Asia/Dhaka"

@lru_cache()
def get_settings() -> Settings:
    return Settings(
        DISCORD_PUBLIC_KEY=os.getenv("DISCORD_PUBLIC_KEY", ""),
        DISCORD_APPLICATION_ID=os.getenv("DISCORD_APPLICATION_ID", ""),
        DISCORD_BOT_TOKEN=os.getenv("DISCORD_BOT_TOKEN", ""),
        DISCORD_GUILD_ID=os.getenv("DISCORD_GUILD_ID", ""),
        DYNAMODB_TABLE_NAME=os.getenv("DYNAMODB_TABLE_NAME", "MHP-Data"),
        S3_BUCKET=os.getenv("S3_BUCKET", "mhp-reports"),
        S3_PREFIX=os.getenv("S3_PREFIX", "reports/"),
        CUTOFF_TIME=os.getenv("CUTOFF_TIME", "21:00"),
        WFH_MONTHLY_CAP=int(os.getenv("WFH_MONTHLY_CAP", "5")),
        FORWARD_PLANNING_DAYS=int(os.getenv("FORWARD_PLANNING_DAYS", "7")),
        TIMEZONE=os.getenv("TIMEZONE", "Asia/Dhaka"),
    )
settings = get_settings()
