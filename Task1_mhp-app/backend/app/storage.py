import json
import os
from datetime import date, datetime
from typing import Optional, Dict, List
from pathlib import Path
from app.models import User, MealParticipation, MealType, create_default_participation

DATA_DIR = Path(__file__).parent.parent / "data"
USERS_FILE = DATA_DIR / "users.json"
PARTICIPATION_FILE = DATA_DIR / "participation.json"

DATA_DIR.mkdir(exist_ok=True)

def _serialize_datetime(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def _load_json(filepath: Path) -> dict:
    if not filepath.exists():
        return {"users": []} if "users" in str(filepath) else {"participation": []}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"users": []} if "users" in str(filepath) else {"participation": []}
    
def _save_json(filepath: Path, data: dict) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=_serialize_datetime, ensure_ascii=False)

# ===========================
# User Operations
# ===========================

def get_all_users() -> List[User]:
    data = _load_json(USERS_FILE)
    return [User(**user) for user in data.get("users", [])]

def get_user_by_id(user_id: str) -> Optional[User]:
    users = get_all_users()
    for user in users:
        if user.id == user_id:
            return user
    return None

def get_user_by_email(email: str) -> Optional[User]:
    users = get_all_users()
    for user in users:
        if user.email.lower() == email.lower():
            return user
    return None

def create_user(user: User) -> User:
    if get_user_by_email(user.email):
        raise ValueError(f"User with email {user.email} already exists.")
    data = _load_json(USERS_FILE)
    users = data.get("users", [])

    user_dict = user.model_dump(mode="json")
    users.append(user_dict)
    data["users"] = users
    _save_json(USERS_FILE, data)

    return user

def update_user(user: User) -> User:
    data = _load_json(USERS_FILE)
    users = data.get("users", [])

    found = False
    for i, u in enumerate(users):
        if u["id"] == user.id:
            users[i] = user.model_dump(mode="json")
            found = True
            break
    if not found:
        raise ValueError(f"User with id {user.id} not found.")
    
    data["users"] = users
    _save_json(USERS_FILE, data)

    return user

# ===========================
# Meal Participation Operations
# ===========================

def get_all_participation() -> List[MealParticipation]:
    data = _load_json(PARTICIPATION_FILE)
    participation_list = []

    for record in data.get("participation", []):
        if isinstance(record.get("date"), str):
            record["date"] = datetime.fromisoformat(record["date"]).date()
        if isinstance(record.get("updated_at"), str):
            record["updated_at"] = datetime.fromisoformat(record["updated_at"])

        participation_list.append(MealParticipation(**record))

    return participation_list

def get_user_participation(user_id: str, target_date: date) -> List[MealParticipation]:
    all_participation = get_all_participation()
    user_records = [
        p for p in all_participation
        if p.user_id == user_id and p.date == target_date
    ]

    if not user_records:
        user_records = create_default_participation(user_id, target_date)
        for record in user_records:
            create_participation(record)

    return user_records

def get_participation_by_date(target_date:date) -> List[MealParticipation]:
    all_participation = get_all_participation()
    return [p for p in all_participation if p.date == target_date]

def create_participation(participation: MealParticipation) -> MealParticipation:
    data = _load_json(PARTICIPATION_FILE)
    records = data.get("participation", [])
    record_dict = participation.model_dump(mode="json")
    records.append(record_dict)

    data["participation"] = records
    _save_json(PARTICIPATION_FILE, data)

    return participation

def update_participation(
        user_id: str,
        target_date: date,
        meal_type: MealType,
        is_participating: bool,
        updated_by: str
) -> MealParticipation:
    data = _load_json(PARTICIPATION_FILE)
    records = data.get("participation", [])

    found = False
    for record in records:
        record_date = record.get("date")
        if isinstance(record_date, str):
            record_date = datetime.fromisoformat(record_date).date()

        if (record["user_id"] == user_id and
            record_date == target_date and
            record["meal_type"] == meal_type.value):
            record["is_participating"] = is_participating
            record["updated_by"] = updated_by
            record["updated_at"] = datetime.now().isoformat()
            found = True
            
            data["participation"] = records
            _save_json(PARTICIPATION_FILE, data)

            record["date"] = record_date
            record["updated_at"] = datetime.fromisoformat(record["updated_at"])
            return MealParticipation(**record)
        
    if not found:
        new_record = MealParticipation(
            user_id=user_id,
            meal_type=meal_type,
            date=target_date,
            is_participating=is_participating,
            updated_by=updated_by,
            updated_at=datetime.now()
        )
        return create_participation(new_record)
    
def get_headcount_by_date(target_date: date) -> Dict[str, int]:
    participation_records = get_participation_by_date(target_date)
    headcount = {meal_type.value: 0 for meal_type in MealType}

    for record in participation_records:
        if record.is_participating:
            headcount[record.meal_type.value] += 1

    return headcount


def get_users_by_team(team: str) -> List[User]:
    """Get all users in a specific team"""
    all_users = get_all_users()
    return [u for u in all_users if u.team and u.team.lower() == team.lower()]


def get_headcount_by_date_and_team(target_date: date, team: str) -> Dict[str, int]:
    """Get headcount filtered by team for a specific date"""
    team_users = get_users_by_team(team)
    team_user_ids = {u.id for u in team_users}
    participation_records = get_participation_by_date(target_date)
    headcount = {meal_type.value: 0 for meal_type in MealType}

    for record in participation_records:
        if record.is_participating and record.user_id in team_user_ids:
            headcount[record.meal_type.value] += 1

    return headcount

def initialize_daily_participation(target_date: date) -> None:
    all_users = get_all_users()
    for user in all_users:
        if not user.is_active:
            continue

        existing = get_user_participation(user.id, target_date)
        pass # If no records exist, they'll be created by get_user_participation

# ===========================
# Initialization and Seeding
# ===========================

def seed_initial_data() -> None:
    from passlib.context import CryptContext
    from app.models import UserRole
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    if get_all_users():
        print("Data already exists. Skipping seed.")
        return
    
    test_users = [
        User(
            name="Employee Test",
            email="employee@test.com",
            password_hash=pwd_context.hash("employee"),
            role=UserRole.EMPLOYEE,
            team="Engineering"
        ),
        User(
            name="Team Lead Test",
            email="teamlead@test.com",
            password_hash=pwd_context.hash("teamlead"),
            role=UserRole.TEAM_LEAD,
            team="Engineering"
        ),
        User(
            name="Admin Test",
            email="admin@company.com",
            password_hash=pwd_context.hash("admin123"),
            role=UserRole.ADMIN,
            team="Operations"
        ),
    ]
    
    for user in test_users:
        create_user(user)
        print(f"Created user: {user.email}")
    
    today = date.today()
    initialize_daily_participation(today)
    print(f"Initialized participation for {today}")
    
    print("Seed data created successfully!")


if __name__ == "__main__":
    # Run seed data when this module is executed directly
    seed_initial_data()
