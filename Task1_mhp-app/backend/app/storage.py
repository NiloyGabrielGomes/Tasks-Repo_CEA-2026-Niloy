import json
import os
from datetime import date, datetime
from typing import Optional, Dict, List
from pathlib import Path
from app.models import User, MealParticipation, MealType, WorkLocation, WorkLocationType, SpecialDay, DayType, create_default_participation, ADMIN_CONTROLLED_MEALS

DATA_DIR = Path(__file__).parent.parent / "data"
USERS_FILE = DATA_DIR / "users.json"
PARTICIPATION_FILE = DATA_DIR / "meal_participation.json"
MEAL_CONFIG_FILE = DATA_DIR / "meal_config.json"
WORK_LOCATIONS_FILE = DATA_DIR / "work_locations.json"
SPECIAL_DAYS_FILE = DATA_DIR / "special_days.json"

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
    """Pre-create default participation records for all active users on the given date.

    For each active user, any meal types that do not already have a record for
    *target_date* will get a new default record (opted-in or opted-out based on
    DEFAULT_OPTED_IN_MEALS).  Users who already have full records are skipped.
    """
    all_users = get_all_users()
    all_participation = get_all_participation()

    # Build a lookup of existing records: { (user_id, meal_type_value) }
    existing_keys = {
        (p.user_id, p.meal_type.value)
        for p in all_participation
        if p.date == target_date
    }

    for user in all_users:
        if not user.is_active:
            continue

        defaults = create_default_participation(user.id, target_date)
        for record in defaults:
            if (record.user_id, record.meal_type.value) not in existing_keys:
                create_participation(record)


# ===========================
# Work Location Operations
# ===========================

def _load_work_locations() -> List[dict]:
    data = _load_json(WORK_LOCATIONS_FILE)
    return data.get("locations", [])


def _save_work_locations(locations: List[dict]) -> None:
    _save_json(WORK_LOCATIONS_FILE, {"locations": locations})


def get_work_location(user_id: str, target_date: date) -> Optional[WorkLocation]:
    """Get a user's work location for a specific date."""
    locations = _load_work_locations()
    for loc in locations:
        loc_date = loc.get("date")
        if isinstance(loc_date, str):
            loc_date = datetime.fromisoformat(loc_date).date()
        if loc["user_id"] == user_id and loc_date == target_date:
            loc["date"] = loc_date
            if isinstance(loc.get("updated_at"), str):
                loc["updated_at"] = datetime.fromisoformat(loc["updated_at"])
            return WorkLocation(**loc)
    return None


def set_work_location(
    user_id: str,
    target_date: date,
    location: WorkLocationType,
    updated_by: str
) -> WorkLocation:
    locations = _load_work_locations()
    now = datetime.now()

    for loc in locations:
        loc_date = loc.get("date")
        if isinstance(loc_date, str):
            loc_date = datetime.fromisoformat(loc_date).date()
        if loc["user_id"] == user_id and loc_date == target_date:
            loc["location"] = location.value
            loc["updated_by"] = updated_by
            loc["updated_at"] = now.isoformat()
            _save_work_locations(locations)
            loc["date"] = loc_date
            loc["updated_at"] = now
            return WorkLocation(**loc)

    new_loc = WorkLocation(
        user_id=user_id,
        date=target_date,
        location=location,
        updated_by=updated_by,
        updated_at=now,
    )
    locations.append(new_loc.model_dump(mode="json"))
    _save_work_locations(locations)
    return new_loc


def get_work_locations_by_date(target_date: date) -> List[WorkLocation]:
    locations = _load_work_locations()
    results = []
    for loc in locations:
        loc_date = loc.get("date")
        if isinstance(loc_date, str):
            loc_date = datetime.fromisoformat(loc_date).date()
        if loc_date == target_date:
            loc["date"] = loc_date
            if isinstance(loc.get("updated_at"), str):
                loc["updated_at"] = datetime.fromisoformat(loc["updated_at"])
            results.append(WorkLocation(**loc))
    return results


def get_team_participation(team: str, target_date: date) -> List[dict]:

    team_users = get_users_by_team(team)
    participation_records = get_participation_by_date(target_date)
    work_locations = get_work_locations_by_date(target_date)
    enabled_types = get_enabled_meal_types()

    user_participation: Dict[str, Dict[str, bool]] = {}
    for p in participation_records:
        if p.meal_type.value in [mt.value if hasattr(mt, 'value') else mt for mt in enabled_types]:
            user_participation.setdefault(p.user_id, {})[p.meal_type.value] = p.is_participating

    user_locations: Dict[str, str] = {}
    for wl in work_locations:
        user_locations[wl.user_id] = wl.location.value if hasattr(wl.location, 'value') else wl.location

    result = []
    for user in team_users:
        if not user.is_active:
            continue
        result.append({
            "user_id": user.id,
            "user_name": user.name,
            "email": user.email,
            "work_location": user_locations.get(user.id, "Office"),
            "meals": user_participation.get(user.id, {}),
        })

    return result


def get_all_teams() -> List[str]:
    users = get_all_users()
    teams = {u.team for u in users if u.team}
    return sorted(teams)

# ===========================
# Meal Configuration (Admin-controlled meal types)
# ===========================

def _load_meal_config() -> Dict[str, bool]:
    """Load meal config. Returns dict of meal_type -> enabled."""
    if not MEAL_CONFIG_FILE.exists():
        # By default, admin-controlled meals are disabled
        default = {}
        for mt in MealType:
            default[mt.value] = mt not in ADMIN_CONTROLLED_MEALS
        return default
    try:
        with open(MEAL_CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("enabled_meals", {})
    except json.JSONDecodeError:
        default = {}
        for mt in MealType:
            default[mt.value] = mt not in ADMIN_CONTROLLED_MEALS
        return default

def _save_meal_config(config: Dict[str, bool]) -> None:
    _save_json(MEAL_CONFIG_FILE, {"enabled_meals": config})

def get_enabled_meals() -> Dict[str, bool]:
    """Get which meal types are currently enabled."""
    return _load_meal_config()

def set_meal_enabled(meal_type: str, enabled: bool) -> Dict[str, bool]:
    """Enable or disable a meal type. Returns updated config."""
    config = _load_meal_config()
    config[meal_type] = enabled
    _save_meal_config(config)
    return config

def get_enabled_meal_types() -> List[str]:
    """Get list of meal type values that are currently enabled."""
    config = _load_meal_config()
    return [mt for mt, enabled in config.items() if enabled]


# ===========================
# Special Day Operations
# ===========================

def _load_special_days() -> List[dict]:
    data = _load_json(SPECIAL_DAYS_FILE)
    return data.get("special_days", [])


def _save_special_days(days: List[dict]) -> None:
    _save_json(SPECIAL_DAYS_FILE, {"special_days": days})


def create_special_day(special_day: SpecialDay) -> SpecialDay:
    days = _load_special_days()

    # Check for duplicate date
    for d in days:
        d_date = d.get("date")
        if isinstance(d_date, str):
            d_date = datetime.fromisoformat(d_date).date() if "T" in d_date else date.fromisoformat(d_date)
        sd_date = special_day.date
        if isinstance(sd_date, str):
            sd_date = date.fromisoformat(sd_date)
        if d_date == sd_date:
            raise ValueError(f"A special day already exists for {special_day.date}")

    days.append(special_day.model_dump(mode="json"))
    _save_special_days(days)
    return special_day


def get_special_day_by_date(target_date: date) -> Optional[SpecialDay]:
    days = _load_special_days()
    for d in days:
        d_date = d.get("date")
        if isinstance(d_date, str):
            d_date = datetime.fromisoformat(d_date).date() if "T" in d_date else date.fromisoformat(d_date)
        if d_date == target_date:
            d["date"] = d_date
            if isinstance(d.get("created_at"), str):
                d["created_at"] = datetime.fromisoformat(d["created_at"])
            return SpecialDay(**d)
    return None


def get_special_days_range(start_date: date, end_date: date) -> List[SpecialDay]:
    days = _load_special_days()
    results = []
    for d in days:
        d_date = d.get("date")
        if isinstance(d_date, str):
            d_date = datetime.fromisoformat(d_date).date() if "T" in d_date else date.fromisoformat(d_date)
        if start_date <= d_date <= end_date:
            d["date"] = d_date
            if isinstance(d.get("created_at"), str):
                d["created_at"] = datetime.fromisoformat(d["created_at"])
            results.append(SpecialDay(**d))
    return results


def delete_special_day(special_day_id: str) -> bool:
    days = _load_special_days()
    original_len = len(days)
    days = [d for d in days if d.get("id") != special_day_id]
    if len(days) == original_len:
        return False
    _save_special_days(days)
    return True


def is_participation_blocked(target_date: date) -> tuple[bool, str | None]:
    sd = get_special_day_by_date(target_date)
    if sd is None:
        return False, None

    day_type = sd.day_type
    if isinstance(day_type, str):
        day_type_val = day_type
    else:
        day_type_val = day_type.value if hasattr(day_type, "value") else str(day_type)

    if day_type_val in (DayType.OFFICE_CLOSED.value, DayType.GOVERNMENT_HOLIDAY.value):
        label = "Office Closed" if day_type_val == DayType.OFFICE_CLOSED.value else "Government Holiday"
        reason = f"Meal participation is not available: {label}"
        if sd.note:
            reason += f" — {sd.note}"
        return True, reason

    return False, None

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
    
    if not SPECIAL_DAYS_FILE.exists():
        _save_json(SPECIAL_DAYS_FILE, {"special_days": []})
        print("Initialized special_days.json")

    print("Seed data created successfully!")


if __name__ == "__main__":
    # Run seed data when this module is executed directly
    seed_initial_data()
