import os
from datetime import date, datetime
from typing import Optional

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

from src.config import settings
from src.models import (
    User, MealParticipation, WorkLocation, SpecialDay, Policy,
    UserRole, MealType, WorkLocationType, DayType,
    ExternalIdentity, Team,
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
            return _parse_user_item(item)
        except ClientError:
            return None

    def put_user(self, user: User) -> None:
        self.table.put_item(Item={
            "PK": f"USER#{user.user_id}",
            "SK": "PROFILE",
            "user_id": user.user_id,
            "name": user.name,
            "email": user.email,
            "role": user.role.value,
            "team": user.team,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
            "GSI2PK": "USER",
            "GSI2SK": f"{user.created_at.isoformat()}#{user.user_id}",
        })

    def upsert_user(self, user: User) -> None:
        """Update mutable fields; set created_at only on first write."""
        now = user.created_at.isoformat()
        self.table.update_item(
            Key={"PK": f"USER#{user.user_id}", "SK": "PROFILE"},
            UpdateExpression=(
                "SET #n = :name, #r = :role, #t = :team, "
                "is_active = :is_active, user_id = :user_id, "
                "GSI2PK = :gsi2pk, GSI2SK = :gsi2sk, "
                "created_at = if_not_exists(created_at, :created_at)"
            ),
            ExpressionAttributeNames={"#n": "name", "#r": "role", "#t": "team"},
            ExpressionAttributeValues={
                ":name": user.name,
                ":role": user.role.value,
                ":team": user.team,
                ":is_active": user.is_active,
                ":user_id": user.user_id,
                ":gsi2pk": "USER",
                ":gsi2sk": f"{now}#{user.user_id}",
                ":created_at": now,
            },
        )

    def get_user_team(self, discord_id: str) -> Optional[str]:
        user = self.get_user(discord_id)
        return user.team if user else None

    def get_canonical_user_id(self, provider: str, external_id: str) -> Optional[str]:
        try:
            resp = self.table.get_item(
                Key={
                    "PK": f"IDENT#{provider}#{external_id}",
                    "SK": f"IDENT#{provider}#{external_id}",
                }
            )
            item = resp.get("Item")
            return item["user_id"] if item else None
        except ClientError:
            return None

    def get_user_by_identity(self, provider: str, external_id: str) -> Optional[User]:
        try:
            resp = self.table.get_item(
                Key={
                    "PK": f"IDENT#{provider}#{external_id}",
                    "SK": f"IDENT#{provider}#{external_id}",
                }
            )
            item = resp.get("Item")
            if not item:
                return None
            return self.get_user(item["user_id"])
        except ClientError:
            return None

    def get_all_users(self) -> list[User]:
        users = []
        try:
            resp = self.table.query(
                IndexName="GSI2",
                KeyConditionExpression=Key("GSI2PK").eq("USER")
            )
            for item in resp.get("Items", []):
                users.append(_parse_user_item(item))
        except ClientError as e:
            print(f"Error listing users: {e}")
        return users

    def get_users_by_team(self, team_name: str) -> list[User]:
        return [u for u in self.get_all_users() if u.team == team_name]

    # ── External Identity ────────────────────────────────────────────────────

    def put_identity(self, identity: ExternalIdentity) -> None:
        self.table.put_item(Item={
            "PK": f"IDENT#{identity.provider}#{identity.external_id}",
            "SK": f"IDENT#{identity.provider}#{identity.external_id}",
            "provider": identity.provider,
            "external_id": identity.external_id,
            "user_id": identity.user_id,
        })

    # ── Team Operations ──────────────────────────────────────────────────────

    def put_team(self, team: Team) -> None:
        self.table.put_item(Item={
            "PK": f"TEAM#{team.team_id}",
            "SK": "METADATA",
            "team_id": team.team_id,
            "team_name": team.team_name,
            "created_at": team.created_at.isoformat(),
            "GSI2PK": "TEAM",
            "GSI2SK": f"{team.team_name}#{team.team_id}",
        })

    def get_team(self, team_id: str) -> Optional[Team]:
        try:
            resp = self.table.get_item(
                Key={"PK": f"TEAM#{team_id}", "SK": "METADATA"}
            )
            item = resp.get("Item")
            if not item:
                return None
            return Team(
                team_id=item["team_id"],
                team_name=item["team_name"],
                created_at=datetime.fromisoformat(item["created_at"])
            )
        except ClientError:
            return None

    def get_all_teams(self) -> list[Team]:
        teams = []
        try:
            resp = self.table.query(
                IndexName="GSI2",
                KeyConditionExpression=Key("GSI2PK").eq("TEAM")
            )
            for item in resp.get("Items", []):
                teams.append(Team(
                    team_id=item["team_id"],
                    team_name=item["team_name"],
                    created_at=datetime.fromisoformat(item["created_at"])
                ))
        except ClientError as e:
            print(f"Error listing teams: {e}")
        return teams

    # ── Meal Participation ───────────────────────────────────────────────────

    def get_meal(
        self,
        discord_id: str,
        meal_date: date,
        meal_type: MealType,
    ) -> Optional[MealParticipation]:
        try:
            resp = self.table.get_item(
                Key={
                    "PK": f"USER#{discord_id}",
                    "SK": f"MEAL#{meal_date.isoformat()}#{meal_type.value}",
                }
            )
            item = resp.get("Item")
            if not item:
                return None
            return _parse_meal_item(item)
        except ClientError:
            return None

    def put_meal(self, meal: MealParticipation) -> None:
        item = {
            "PK": f"USER#{meal.user_id}",
            "SK": f"MEAL#{meal.date.isoformat()}#{meal.meal_type.value}",
            "user_id": meal.user_id,
            "date": meal.date.isoformat(),
            "meal_type": meal.meal_type.value,
            "is_participating": meal.is_participating,
            "updated_by": meal.updated_by,
            "updated_at": meal.updated_at.isoformat(),
            "reason": meal.reason,
            "GSI1PK": f"DATE#{meal.date.isoformat()}",
            "GSI1SK": f"MEAL#{meal.user_id}#{meal.meal_type.value}",
        }
        if meal.team:
            item["team"] = meal.team
        self.table.put_item(Item=item)

    def get_meals_for_date(self, meal_date: date) -> list[MealParticipation]:
        meals = []
        try:
            resp = self.table.query(
                IndexName="GSI1",
                KeyConditionExpression=(
                    Key("GSI1PK").eq(f"DATE#{meal_date.isoformat()}") &
                    Key("GSI1SK").begins_with("MEAL#")
                )
            )
            for item in resp.get("Items", []):
                meals.append(_parse_meal_item(item))
        except ClientError as e:
            print(f"Error querying meals: {e}")
        return meals

    def get_meals_for_date_and_team(
        self, meal_date: date, team_name: str
    ) -> list[MealParticipation]:
        meals = []
        try:
            resp = self.table.query(
                IndexName="GSI1",
                KeyConditionExpression=(
                    Key("GSI1PK").eq(f"DATE#{meal_date.isoformat()}") &
                    Key("GSI1SK").begins_with("MEAL#")
                ),
                FilterExpression=Attr("team").eq(team_name)
            )
            for item in resp.get("Items", []):
                meals.append(_parse_meal_item(item))
        except ClientError as e:
            print(f"Error querying team meals: {e}")
        return meals

    def get_meals_for_user(
        self, discord_id: str, start_date: date = None
    ) -> list[MealParticipation]:
        meals = []
        try:
            kce = Key("PK").eq(f"USER#{discord_id}") & Key("SK").begins_with("MEAL#")
            resp = self.table.query(KeyConditionExpression=kce)
            for item in resp.get("Items", []):
                meal_date = date.fromisoformat(item["date"])
                if start_date is None or meal_date >= start_date:
                    meals.append(_parse_meal_item(item))
        except ClientError as e:
            print(f"Error querying user meals: {e}")
        return meals

    # ── Work Location ───────────────────────────────────────────────────────

    def get_location(
        self,
        discord_id: str,
        location_date: date,
    ) -> Optional[WorkLocation]:
        try:
            resp = self.table.get_item(
                Key={
                    "PK": f"USER#{discord_id}",
                    "SK": f"WORKLOC#{location_date.isoformat()}",
                }
            )
            item = resp.get("Item")
            if not item:
                return None
            return _parse_location_item(item)
        except ClientError:
            return None

    def put_location(self, location: WorkLocation) -> None:
        item = {
            "PK": f"USER#{location.user_id}",
            "SK": f"WORKLOC#{location.date.isoformat()}",
            "user_id": location.user_id,
            "date": location.date.isoformat(),
            "location": location.location.value,
            "updated_by": location.updated_by,
            "updated_at": location.updated_at.isoformat(),
            "GSI1PK": f"DATE#{location.date.isoformat()}",
            "GSI1SK": f"WORKLOC#{location.user_id}",
        }
        if location.team:
            item["team"] = location.team
        self.table.put_item(Item=item)

    def get_locations_for_date(self, location_date: date) -> list[WorkLocation]:
        locations = []
        try:
            resp = self.table.query(
                IndexName="GSI1",
                KeyConditionExpression=(
                    Key("GSI1PK").eq(f"DATE#{location_date.isoformat()}") &
                    Key("GSI1SK").begins_with("WORKLOC#")
                )
            )
            for item in resp.get("Items", []):
                locations.append(_parse_location_item(item))
        except ClientError as e:
            print(f"Error querying locations: {e}")
        return locations

    def get_locations_for_date_and_team(
        self, location_date: date, team_name: str
    ) -> list[WorkLocation]:
        locations = []
        try:
            resp = self.table.query(
                IndexName="GSI1",
                KeyConditionExpression=(
                    Key("GSI1PK").eq(f"DATE#{location_date.isoformat()}") &
                    Key("GSI1SK").begins_with("WORKLOC#")
                ),
                FilterExpression=Attr("team").eq(team_name)
            )
            for item in resp.get("Items", []):
                locations.append(_parse_location_item(item))
        except ClientError as e:
            print(f"Error querying team locations: {e}")
        return locations

    def get_locations_for_date_range(
        self, discord_id: str, start_date: date, end_date: date
    ) -> list[WorkLocation]:
        locations = []
        try:
            resp = self.table.query(
                KeyConditionExpression=(
                    Key("PK").eq(f"USER#{discord_id}") &
                    Key("SK").between(
                        f"WORKLOC#{start_date.isoformat()}",
                        f"WORKLOC#{end_date.isoformat()}",
                    )
                )
            )
            for item in resp.get("Items", []):
                locations.append(_parse_location_item(item))
        except ClientError as e:
            print(f"Error querying location range: {e}")
        return locations

    # ── Special Day ─────────────────────────────────────────────────────────

    def get_special_day(self, special_date: date) -> Optional[SpecialDay]:
        try:
            resp = self.table.get_item(
                Key={"PK": f"DAY#{special_date.isoformat()}", "SK": "METADATA"}
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
        year_month = special_day.date.strftime("%Y-%m")
        self.table.put_item(Item={
            "PK": f"DAY#{special_day.date.isoformat()}",
            "SK": "METADATA",
            "date": special_day.date.isoformat(),
            "day_type": special_day.day_type.value,
            "note": special_day.note,
            "GSI2PK": f"SPECIALDAY#{year_month}",
            "GSI2SK": f"DAY#{special_day.date.isoformat()}",
        })

    def get_special_days_for_month(self, year_month: str) -> list[SpecialDay]:
        special_days = []
        try:
            resp = self.table.query(
                IndexName="GSI2",
                KeyConditionExpression=Key("GSI2PK").eq(f"SPECIALDAY#{year_month}")
            )
            for item in resp.get("Items", []):
                special_days.append(SpecialDay(
                    date=date.fromisoformat(item["date"]),
                    day_type=DayType(item["day_type"]),
                    note=item.get("note")
                ))
        except ClientError as e:
            print(f"Error querying special days: {e}")
        return special_days

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

# ── Private helpers ──────────────────────────────────────────────────────────

def _parse_user_item(item: dict) -> User:
    return User(
        user_id=item.get("user_id") or item.get("discord_id", ""),  # backwards compat
        name=item["name"],
        email=item.get("email"),
        role=UserRole(item.get("role", "employee")),
        team=item.get("team"),
        is_active=item.get("is_active", True),
        created_at=datetime.fromisoformat(item["created_at"])
    )

def _parse_meal_item(item: dict) -> MealParticipation:
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

def _parse_location_item(item: dict) -> WorkLocation:
    return WorkLocation(
        user_id=item["user_id"],
        date=date.fromisoformat(item["date"]),
        location=WorkLocationType(item["location"]),
        team=item.get("team"),
        updated_by=item.get("updated_by"),
        updated_at=datetime.fromisoformat(item["updated_at"])
    )
# Singleton instance
storage = DynamoDBStorage()
