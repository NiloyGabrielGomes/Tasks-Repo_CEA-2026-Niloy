from datetime import date, datetime
from typing import Optional, Dict, List
from sqlmodel import Session, select, col
from app.database import engine
from app.models import (
    User, MealParticipation, MealType, WorkLocation, WorkLocationType, 
    SpecialDay, DayType, create_default_participation, 
    ADMIN_CONTROLLED_MEALS, DEFAULT_OPTED_IN_MEALS
)
from app import utils
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
MEAL_CONFIG_FILE = DATA_DIR / "meal_config.json"
DATA_DIR.mkdir(exist_ok=True)


# ===========================
# User Operations
# ===========================

def get_all_users() -> List[User]:
    with Session(engine) as session:
        return session.exec(select(User)).all()

def get_user_by_id(user_id: str) -> Optional[User]:
    with Session(engine) as session:
        return session.get(User, user_id)

def get_user_by_email(email: str) -> Optional[User]:
    with Session(engine) as session:
        statement = select(User).where(User.email == email)
        return session.exec(statement).first()

def create_user(user: User) -> User:
    with Session(engine) as session:
        if session.exec(select(User).where(User.email == user.email)).first():
            raise ValueError(f"User with email {user.email} already exists.")
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

def update_user(user: User) -> User:
    with Session(engine) as session:
        db_user = session.get(User, user.id)
        if not db_user:
            raise ValueError(f"User with id {user.id} not found.")
        
        user_data = user.model_dump(exclude_unset=True)
        for key, value in user_data.items():
            setattr(db_user, key, value)
        
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user

# ===========================
# Meal Participation Operations
# ===========================

def get_all_participation() -> List[MealParticipation]:
    with Session(engine) as session:
        return session.exec(select(MealParticipation)).all()

def get_user_participation(user_id: str, target_date: date) -> List[MealParticipation]:
    with Session(engine) as session:
        statement = select(MealParticipation).where(
            MealParticipation.user_id == user_id,
            MealParticipation.date == target_date
        )
        results = session.exec(statement).all()
        
        if not results:
            defaults = create_default_participation(user_id, target_date)
            for d in defaults:
                session.add(d)
            session.commit()
            
            # Re-query ensure we get fresh objects
            results = session.exec(statement).all()
            
        return results

def get_participation_by_date(target_date: date) -> List[MealParticipation]:
    with Session(engine) as session:
        statement = select(MealParticipation).where(MealParticipation.date == target_date)
        return session.exec(statement).all()

def create_participation(participation: MealParticipation) -> MealParticipation:
    with Session(engine) as session:
        session.add(participation)
        session.commit()
        session.refresh(participation)
        return participation

def update_participation(
        user_id: str,
        target_date: date,
        meal_type: MealType,
        is_participating: bool,
        updated_by: str,
        reason: str = None
) -> MealParticipation:
    
    with Session(engine) as session:
        statement = select(MealParticipation).where(
            MealParticipation.user_id == user_id,
            MealParticipation.date == target_date,
            MealParticipation.meal_type == meal_type
        )
        record = session.exec(statement).first()
        
        if record:
            record.is_participating = is_participating
            record.updated_by = updated_by
            record.updated_at = datetime.utcnow()
            if reason is not None:
                record.reason = reason
            session.add(record)
            session.commit()
            session.refresh(record)
            return record
        else:
            new_record = MealParticipation(
                user_id=user_id,
                meal_type=meal_type,
                date=target_date,
                is_participating=is_participating,
                updated_by=updated_by,
                updated_at=datetime.utcnow(),
                reason=reason,
            )
            session.add(new_record)
            session.commit()
            session.refresh(new_record)
            return new_record


def bulk_update_participation(
    user_ids: list[str],
    target_date: date,
    meals: dict[str, bool],
    updated_by: str,
    reason: str = None,
) -> tuple[int, list[dict]]:

    succeeded = 0
    failed = []
    
    enabled = get_enabled_meal_types()

    with Session(engine) as session:
        for uid in user_ids:
            user = session.get(User, uid)
            if not user:
                failed.append({"user_id": uid, "error": "User not found"})
                continue
                
            for meal_key, participating in meals.items():
                try:
                    meal_enum = MealType(meal_key)
                except ValueError:
                    failed.append({"user_id": uid, "error": f"Invalid meal type: {meal_key}"})
                    continue
                
                if meal_enum not in enabled:
                    failed.append({"user_id": uid, "error": f"{meal_key} is not enabled"})
                    continue
                
                # Update logic inline to reuse the session
                statement = select(MealParticipation).where(
                    MealParticipation.user_id == uid,
                    MealParticipation.date == target_date,
                    MealParticipation.meal_type == meal_enum
                )
                record = session.exec(statement).first()
                
                if record:
                    record.is_participating = participating
                    record.updated_by = updated_by
                    record.updated_at = datetime.utcnow()
                    if reason is not None:
                        record.reason = reason
                    session.add(record)
                else:
                    new_record = MealParticipation(
                        user_id=uid,
                        meal_type=meal_enum,
                        date=target_date,
                        is_participating=participating,
                        updated_by=updated_by,
                        updated_at=datetime.utcnow(),
                        reason=reason,
                    )
                    session.add(new_record)
                
                succeeded += 1
        
        session.commit() # Commit all changes at once at the end

                
    return succeeded, failed

def get_headcount_by_date(target_date: date) -> Dict[str, int]:
    with Session(engine) as session:
        statement = select(MealParticipation).where(
            MealParticipation.date == target_date,
            MealParticipation.is_participating == True
        )
        records = session.exec(statement).all()
        
        headcount = {meal_type.value: 0 for meal_type in MealType}
        for record in records:
            headcount[record.meal_type.value] += 1
            
        return headcount


def get_users_by_team(team: str) -> List[User]:
    with Session(engine) as session:
        statement = select(User).where(col(User.team).ilike(team)) # Case insensitive if supported or check logic
        all_users = session.exec(select(User)).all()
        return [u for u in all_users if u.team and u.team.lower() == team.lower()]


def get_headcount_by_date_and_team(target_date: date, team: str) -> Dict[str, int]:
    team_users = get_users_by_team(team)
    team_user_ids = {u.id for u in team_users}
    
    with Session(engine) as session:
        statement = select(MealParticipation).where(
            MealParticipation.date == target_date,
            MealParticipation.is_participating == True,
            col(MealParticipation.user_id).in_(team_user_ids)
        )
        records = session.exec(statement).all()
        
        headcount = {meal_type.value: 0 for meal_type in MealType}
        for record in records:
            headcount[record.meal_type.value] += 1
            
        return headcount

def initialize_daily_participation(target_date: date) -> None:
    all_users = get_all_users()
    
    with Session(engine) as session:
        statement = select(MealParticipation).where(MealParticipation.date == target_date)
        existing = session.exec(statement).all()
        existing_keys = {(p.user_id, p.meal_type) for p in existing}
        
        new_records = []
        for user in all_users:
            if not user.is_active:
                continue
                
            defaults = create_default_participation(user.id, target_date)
            for record in defaults:
                if (record.user_id, record.meal_type) not in existing_keys:
                    session.add(record)
        
        session.commit()


# ===========================
# Work Location Operations
# ===========================

def get_work_location(user_id: str, target_date: date) -> Optional[WorkLocation]:
    with Session(engine) as session:
        statement = select(WorkLocation).where(
            WorkLocation.user_id == user_id,
            WorkLocation.date == target_date
        )
        return session.exec(statement).first()


def set_work_location(
    user_id: str,
    target_date: date,
    location: WorkLocationType,
    updated_by: str
) -> WorkLocation:
    with Session(engine) as session:
        statement = select(WorkLocation).where(
            WorkLocation.user_id == user_id,
            WorkLocation.date == target_date
        )
        record = session.exec(statement).first()
        
        if record:
            record.location = location
            record.updated_by = updated_by
            record.updated_at = datetime.utcnow()
            session.add(record)
            session.commit()
            session.refresh(record)
            return record
        else:
            new_record = WorkLocation(
                user_id=user_id,
                date=target_date,
                location=location,
                updated_by=updated_by,
                updated_at=datetime.utcnow()
            )
            session.add(new_record)
            session.commit()
            session.refresh(new_record)
            return new_record


def get_work_locations_by_date(target_date: date) -> List[WorkLocation]:
    with Session(engine) as session:
        statement = select(WorkLocation).where(WorkLocation.date == target_date)
        return session.exec(statement).all()


def get_team_participation(team: str, target_date: date) -> List[dict]:
    team_users = get_users_by_team(team)
    if not team_users:
        return []
    
    team_user_ids = [u.id for u in team_users]
    enabled_types = get_enabled_meal_types()

    with Session(engine) as session:
        p_stmt = select(MealParticipation).where(
            MealParticipation.date == target_date,
            col(MealParticipation.user_id).in_(team_user_ids)
        )
        participation_records = session.exec(p_stmt).all()
        
        l_stmt = select(WorkLocation).where(
            WorkLocation.date == target_date,
            col(WorkLocation.user_id).in_(team_user_ids)
        )
        work_locations = session.exec(l_stmt).all()

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
    with Session(engine) as session:
        users = session.exec(select(User)).all()
        teams = {u.team for u in users if u.team}
        return sorted(teams)

# ===========================
# Meal Configuration (Admin-controlled meal types)
# ===========================

def _load_meal_config() -> Dict[str, bool]:
    """Load meal config. Returns dict of meal_type -> enabled."""
    if not MEAL_CONFIG_FILE.exists():
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
    with open(MEAL_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"enabled_meals": config}, f, indent=2)

def get_enabled_meals() -> Dict[str, bool]:
    return _load_meal_config()

def set_meal_enabled(meal_type: str, enabled: bool) -> Dict[str, bool]:
    config = _load_meal_config()
    config[meal_type] = enabled
    _save_meal_config(config)
    return config

def get_enabled_meal_types() -> List[str]:
    config = _load_meal_config()
    return [mt for mt, enabled in config.items() if enabled]


# ===========================
# Special Day Operations
# ===========================

def create_special_day(special_day: SpecialDay) -> SpecialDay:
    with Session(engine) as session:
        statement = select(SpecialDay).where(SpecialDay.date == special_day.date)
        existing = session.exec(statement).first()
        if existing:
            raise ValueError(f"A special day already exists for {special_day.date}")
        
        session.add(special_day)
        session.commit()
        session.refresh(special_day)
        return special_day


def get_special_day_by_date(target_date: date) -> Optional[SpecialDay]:
    with Session(engine) as session:
        statement = select(SpecialDay).where(SpecialDay.date == target_date)
        return session.exec(statement).first()


def get_special_days_range(start_date: date, end_date: date) -> List[SpecialDay]:
    with Session(engine) as session:
        statement = select(SpecialDay).where(
            SpecialDay.date >= start_date,
            SpecialDay.date <= end_date
        )
        return session.exec(statement).all()


def delete_special_day(special_day_id: str) -> bool:
    with Session(engine) as session:
        sd = session.get(SpecialDay, special_day_id)
        if not sd:
            return False
        session.delete(sd)
        session.commit()
        return True


def is_participation_blocked(target_date: date) -> tuple[bool, str | None]:
    sd = get_special_day_by_date(target_date)
    if sd is None:
        return False, None

    day_type = sd.day_type
    
    # Handle Enum value or object
    day_type_val = day_type.value if hasattr(day_type, "value") else str(day_type)

    if day_type_val in (DayType.OFFICE_CLOSED.value, DayType.GOVERNMENT_HOLIDAY.value):
        label = "Office Closed" if day_type_val == DayType.OFFICE_CLOSED.value else "Government Holiday"
        reason = f"Meal participation is not available: {label}"
        if sd.note:
            reason += f" — {sd.note}"
        return True, reason

    return False, None
