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
                    region_name=os.getenv("AWS_REGION", "ap-south-1")
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

    # ── Meal Participation ───────────────────────────────────────────────────

    def get_meal(
        self,
        discord_id: str,
        meal_date: date,
        meal_type: MealType
    ) -> Optional[MealParticipation]:
        try:
            resp = self.table.get_item(
                Key={
                    "PK": f"DATE#{meal_date.isoformat()}#MEAL",
                    "SK": f"USER#{discord_id}#{meal_type.value}"
                }
            )
            item = resp.get("Item")
            if not item:
                return None
            return MealParticipation(
                user_id=item["user_id"],
                meal_type=MealType(item["meal_type"]),
                date=date.fromisoformat(item["date"]),
                is_participating=item.get("is_participating", True),
                team=item.get("team"),
                updated_by=item.get("updated_by"),
                updated_at=datetime.fromisoformat(item["updated_at"]),
                reason=item.get("reason")
            )
        except ClientError:
            return None

    def put_meal(self, meal: MealParticipation) -> None:
        item = {
            "PK": f"DATE#{meal.date.isoformat()}#MEAL",
            "SK": f"USER#{meal.user_id}#{meal.meal_type.value}",
            "user_id": meal.user_id,
            "date": meal.date.isoformat(),
            "meal_type": meal.meal_type.value,
            "is_participating": meal.is_participating,
            "updated_by": meal.updated_by,
            "updated_at": meal.updated_at.isoformat(),
            "reason": meal.reason
        }
        if meal.team:
            item["team"] = meal.team
        self.table.put_item(Item=item)

    def get_meals_for_date(self, meal_date: date) -> list[MealParticipation]:
        meals = []
        try:
            resp = self.table.query(
                KeyConditionExpression=Key("PK").eq(f"DATE#{meal_date.isoformat()}#MEAL")
            )
            for item in resp.get("Items", []):
                meals.append(MealParticipation(
                    user_id=item["user_id"],
                    meal_type=MealType(item["meal_type"]),
                    date=date.fromisoformat(item["date"]),
                    is_participating=item.get("is_participating", True),
                    team=item.get("team"),
                    updated_by=item.get("updated_by"),
                    updated_at=datetime.fromisoformat(item["updated_at"]),
                    reason=item.get("reason")
                ))
        except ClientError as e:
            print(f"Error querying meals: {e}")
        return meals

    def get_meals_for_date_and_team(
        self, meal_date: date, team_name: str
    ) -> list[MealParticipation]:
        meals = []
        try:
            resp = self.table.query(
                KeyConditionExpression=Key("PK").eq(f"DATE#{meal_date.isoformat()}#MEAL"),
                FilterExpression="team = :team",
                ExpressionAttributeValues={":team": team_name}
            )
            for item in resp.get("Items", []):
                meals.append(MealParticipation(
                    user_id=item["user_id"],
                    meal_type=MealType(item["meal_type"]),
                    date=date.fromisoformat(item["date"]),
                    is_participating=item.get("is_participating", True),
                    team=item.get("team"),
                    updated_by=item.get("updated_by"),
                    updated_at=datetime.fromisoformat(item["updated_at"]),
                    reason=item.get("reason")
                ))
        except ClientError as e:
            print(f"Error querying team meals: {e}")
        return meals

    def get_meals_for_user(self, discord_id: str, start_date: date = None) -> list[MealParticipation]:
        meals = []
        try:
            resp = self.table.scan(
                FilterExpression="user_id = :uid",
                ExpressionAttributeValues={":uid": discord_id}
            )
            for item in resp.get("Items", []):
                meal_date = date.fromisoformat(item["date"])
                if start_date is None or meal_date >= start_date:
                    meals.append(MealParticipation(
                        user_id=item["user_id"],
                        meal_type=MealType(item["meal_type"]),
                        date=meal_date,
                        is_participating=item.get("is_participating", True),
                        team=item.get("team"),
                        updated_by=item.get("updated_by"),
                        updated_at=datetime.fromisoformat(item["updated_at"]),
                        reason=item.get("reason")
                    ))
        except ClientError as e:
            print(f"Error scanning meals: {e}")
        return meals

    # ── Work Location ───────────────────────────────────────────────────────

    def get_location(
        self,
        discord_id: str,
        location_date: date
    ) -> Optional[WorkLocation]:
        try:
            resp = self.table.get_item(
                Key={
                    "PK": f"DATE#{location_date.isoformat()}#LOCATION",
                    "SK": f"USER#{discord_id}"
                }
            )
            item = resp.get("Item")
            if not item:
                return None
            return WorkLocation(
                user_id=item["user_id"],
                date=date.fromisoformat(item["date"]),
                location=WorkLocationType(item["location"]),
                team=item.get("team"),
                updated_by=item.get("updated_by"),
                updated_at=datetime.fromisoformat(item["updated_at"])
            )
        except ClientError:
            return None

    def put_location(self, location: WorkLocation) -> None:
        item = {
            "PK": f"DATE#{location.date.isoformat()}#LOCATION",
            "SK": f"USER#{location.user_id}",
            "user_id": location.user_id,
            "date": location.date.isoformat(),
            "location": location.location.value,
            "updated_by": location.updated_by,
            "updated_at": location.updated_at.isoformat()
        }
        if location.team:
            item["team"] = location.team
        self.table.put_item(Item=item)

    def get_locations_for_date(self, location_date: date) -> list[WorkLocation]:
        locations = []
        try:
            resp = self.table.query(
                KeyConditionExpression=Key("PK").eq(f"DATE#{location_date.isoformat()}#LOCATION")
            )
            for item in resp.get("Items", []):
                locations.append(WorkLocation(
                    user_id=item["user_id"],
                    date=date.fromisoformat(item["date"]),
                    location=WorkLocationType(item["location"]),
                    team=item.get("team"),
                    updated_by=item.get("updated_by"),
                    updated_at=datetime.fromisoformat(item["updated_at"])
                ))
        except ClientError as e:
            print(f"Error querying locations: {e}")
        return locations

    def get_locations_for_date_and_team(
        self, location_date: date, team_name: str
    ) -> list[WorkLocation]:
        locations = []
        try:
            resp = self.table.query(
                KeyConditionExpression=Key("PK").eq(
                    f"DATE#{location_date.isoformat()}#LOCATION"
                ),
                FilterExpression="team = :team",
                ExpressionAttributeValues={":team": team_name}
            )
            for item in resp.get("Items", []):
                locations.append(WorkLocation(
                    user_id=item["user_id"],
                    date=date.fromisoformat(item["date"]),
                    location=WorkLocationType(item["location"]),
                    team=item.get("team"),
                    updated_by=item.get("updated_by"),
                    updated_at=datetime.fromisoformat(item["updated_at"])
                ))
        except ClientError as e:
            print(f"Error querying team locations: {e}")
        return locations

    # ── Special Day ─────────────────────────────────────────────────────────

    def get_special_day(self, special_date: date) -> Optional[SpecialDay]:
        try:
            resp = self.table.get_item(
                Key={"PK": f"SPECIALDAY#{special_date.isoformat()}", "SK": "-"}
            )
            item = resp.get("Item")
            if not item:
                return None
            return SpecialDay(
                date=date.fromisoformat(item["date"]),
                day_type=DayType(item["day_type"]),
                note=item.get("note")
            )
        except ClientError:
            return None

    def put_special_day(self, special_day: SpecialDay) -> None:
        self.table.put_item(Item={
            "PK": f"SPECIALDAY#{special_day.date.isoformat()}",
            "SK": "-",
            "date": special_day.date.isoformat(),
            "day_type": special_day.day_type.value,
            "note": special_day.note
        })

    # ── Policy ───────────────────────────────────────────────────────────────

    def get_policy(self, policy_name: str) -> Optional[Policy]:
        try:
            resp = self.table.get_item(
                Key={"PK": f"POLICY#{policy_name}", "SK": "-"}
            )
            item = resp.get("Item")
            if not item:
                return None
            return Policy(
                name=item["name"],
                value=item["value"],
                updated_at=datetime.fromisoformat(item["updated_at"])
            )
        except ClientError:
            return None

    def put_policy(self, policy: Policy) -> None:
        self.table.put_item(Item={
            "PK": f"POLICY#{policy.name}",
            "SK": "-",
            "name": policy.name,
            "value": policy.value,
            "updated_at": policy.updated_at.isoformat()
        })
# Singleton instance
storage = DynamoDBStorage()
