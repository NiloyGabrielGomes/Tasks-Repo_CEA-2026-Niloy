from datetime import date, datetime
from typing import Optional, Dict, List
from sqlmodel import Session, select, col
from app.database import engine
from app.models import (
    User, MealParticipation, MealType, WorkLocation, WorkLocationType,
    SpecialDay, DayType, create_default_participation,
    ADMIN_CONTROLLED_MEALS, DEFAULT_OPTED_IN_MEALS,
    Announcement, AnnouncementStatus,
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

def get_headcount_by_team_breakdown(
    target_date: date,
    team_filter: Optional[str] = None,
) -> List[Dict]:
    
    all_users = get_all_users()
    active_users = [u for u in all_users if u.is_active]

    work_locations = get_work_locations_by_date(target_date)
    location_map: Dict[str, WorkLocationType] = {wl.user_id: wl.location for wl in work_locations}

    # Group by team
    teams_map: Dict[str, List[User]] = {}
    for user in active_users:
        team_name = user.team or "Unassigned"
        if team_filter and team_name.lower() != team_filter.lower():
            continue
        teams_map.setdefault(team_name, []).append(user)

    result = []
    for team_name, members in sorted(teams_map.items()):
        office_count = 0
        wfh_count = 0
        member_data = []
        for u in members:
            raw_loc = location_map.get(u.id, WorkLocationType.OFFICE)
            loc_val = raw_loc.value if hasattr(raw_loc, "value") else str(raw_loc)
            if loc_val == WorkLocationType.WFH.value:
                wfh_count += 1
            else:
                office_count += 1
            member_data.append({
                "user_id": u.id,
                "name": u.name,
                "email": u.email,
                "location": loc_val,
            })
        result.append({
            "team": team_name,
            "total_members": len(members),
            "office_count": office_count,
            "wfh_count": wfh_count,
            "members": member_data,
        })
    return result


def get_headcount_by_location_breakdown(
    target_date: date,
    team_filter: Optional[str] = None,
) -> Dict:
    
    all_users = get_all_users()
    active_users = [u for u in all_users if u.is_active]

    if team_filter:
        active_users = [u for u in active_users if u.team and u.team.lower() == team_filter.lower()]

    work_locations = get_work_locations_by_date(target_date)
    location_map: Dict[str, WorkLocationType] = {wl.user_id: wl.location for wl in work_locations}

    office_employees: List[Dict] = []
    wfh_employees: List[Dict] = []

    for user in active_users:
        raw_loc = location_map.get(user.id, WorkLocationType.OFFICE)
        loc_val = raw_loc.value if hasattr(raw_loc, "value") else str(raw_loc)
        entry = {
            "user_id": user.id,
            "name": user.name,
            "email": user.email,
            "team": user.team or "Unassigned",
        }
        if loc_val == WorkLocationType.WFH.value:
            wfh_employees.append(entry)
        else:
            office_employees.append(entry)

    return {
        "total": len(active_users),
        "office_count": len(office_employees),
        "wfh_count": len(wfh_employees),
        "locations": [
            {
                "location": WorkLocationType.OFFICE.value,
                "count": len(office_employees),
                "employees": office_employees,
            },
            {
                "location": WorkLocationType.WFH.value,
                "count": len(wfh_employees),
                "employees": wfh_employees,
            },
        ],
    }


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


# ===========================
# Announcement Operations 
# ===========================

def create_announcement(announcement: Announcement) -> Announcement:
    with Session(engine) as session:
        session.add(announcement)
        session.commit()
        session.refresh(announcement)
        return announcement


def get_announcement_by_id(announcement_id: str) -> Optional[Announcement]:
    with Session(engine) as session:
        return session.get(Announcement, announcement_id)


def get_announcements(
    created_by: str,
    status_filter: Optional[str] = None,
) -> List[Announcement]:

    with Session(engine) as session:
        stmt = select(Announcement).where(Announcement.created_by == created_by)
        if status_filter:
            try:
                status_enum = AnnouncementStatus(status_filter)
                stmt = stmt.where(Announcement.status == status_enum)
            except ValueError:
                pass  # unknown status → return unfiltered
        stmt = stmt.order_by(col(Announcement.created_at).desc())
        return session.exec(stmt).all()


def publish_announcement(
    announcement_id: str,
    scheduled_at: Optional[datetime] = None,
) -> Optional[Announcement]:

    with Session(engine) as session:
        ann = session.get(Announcement, announcement_id)
        if not ann:
            return None
        if ann.status == AnnouncementStatus.SENT:
            return ann  # idempotent — already sent

        now = datetime.utcnow()
        if scheduled_at and scheduled_at > now:
            ann.status = AnnouncementStatus.SCHEDULED
            ann.scheduled_at = scheduled_at
        else:
            ann.status = AnnouncementStatus.SENT
            ann.published_at = now
            ann.scheduled_at = None

        ann.updated_at = now
        session.add(ann)
        session.commit()
        session.refresh(ann)
        return ann
