#DynamoDB Storage Implementation
import os
from datetime import date, datetime
from typing import Optional, Any

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from src.config import settings
from src.models import (
    User, MealParticipation, WorkLocation, SpecialDay, Policy,
    UserRole, MealType, WorkLocationType, DayType
)

class DynamoDBStorage:
    
    def __init__(self, table_name: str = None, dynamodb_resource=None):
        self.table_name = table_name or settings.DYNAMODB_TABLE_NAME
        self._dynamodb_resource = dynamodb_resource
        self._table = None

    @property
    def dynamodb(self):
        if self._dynamodb_resource is None:
            try:
                self._dynamodb_resource = boto3.resource(
                    "dynamodb",
                    region_name=os.getenv("AWS_REGION", "ap-southeast-1")
                )
            except Exception as e:
                raise RuntimeError(
                    f"Failed to initialize DynamoDB resource: {e}. "
                    "Ensure AWS credentials are configured."
                ) from e
        return self._dynamodb_resource

    @property
    def table(self):
        if self._table is None:
            self._table = self.dynamodb.Table(self.table_name)
        return self._table

    # ── User Operations ─────────────────────────────────────────────────────

    def get_user(self, discord_id: str) -> Optional[User]:
        try:
            resp = self.table.get_item(
                Key={"PK": f"USER#{discord_id}", "SK": "PROFILE"}
            )
            item = resp.get("Item")
            if not item:
                return None
            return User(
                discord_id=item["discord_id"],
                name=item["name"],
                email=item.get("email"),
                role=UserRole(item.get("role", "employee")),
                team=item.get("team"),
                is_active=item.get("is_active", True),
                created_at=datetime.fromisoformat(item["created_at"])
            )
        except ClientError:
            return None

    def put_user(self, user: User) -> None:
        self.table.put_item(Item={
            "PK": f"USER#{user.discord_id}",
            "SK": "PROFILE",
            "discord_id": user.discord_id,
            "name": user.name,
            "email": user.email,
            "role": user.role.value,
            "team": user.team,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat()
        })

    def get_user_team(self, discord_id: str) -> Optional[str]:
        user = self.get_user(discord_id)
        return user.team if user else None

    