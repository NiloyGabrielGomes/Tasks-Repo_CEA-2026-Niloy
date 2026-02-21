import sys
from pathlib import Path

# Add backend directory to sys.path so we can import app modules
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from datetime import date, datetime
from sqlmodel import Session, select
from passlib.context import CryptContext

from app.database import engine, create_db_and_tables
from app.models import User, UserRole, MealParticipation, MealType, WorkLocationType, WorkLocation
from app.storage import create_user, initialize_daily_participation

def seed_data():
    print("Creating database and tables...")
    create_db_and_tables()

    # Using pbkdf2_sha256 for bcrypt compatibility issues.
    pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
    
    with Session(engine) as session:
        # Check if users already exist
        # existing_user = session.exec(select(User)).first()
        # if existing_user:
        #     print("Data already exists. Skipping seed.")
        #     return

        print("Seeding users...")
        users = [
            User(
                name="Employee User",
                email="employee@test.com",
                password_hash=pwd_context.hash("employee"),
                role=UserRole.EMPLOYEE,
                team="Engineering",
                is_active=True
            ),
            User(
                name="Team Lead User",
                email="teamlead@test.com",
                password_hash=pwd_context.hash("teamlead"),
                role=UserRole.TEAM_LEAD,
                team="Engineering",
                is_active=True
            ),
            User(
                name="Admin User",
                email="admin@test.com",
                password_hash=pwd_context.hash("admin"),
                role=UserRole.ADMIN,
                team="Operations",
                is_active=True
            ),
            User(
                name="Admin User 2",
                email="admin2@test.com",
                password_hash=pwd_context.hash("admin123"),
                role=UserRole.ADMIN,
                team="Operations",
                is_active=True
            ),
             User(
                name="Niloy User",
                email="niloy@test.com",
                password_hash=pwd_context.hash("niloy"),
                role=UserRole.ADMIN,
                team="Operations",
                is_active=True
            )
        ]

        for user in users:
            existing = session.exec(select(User).where(User.email == user.email)).first()
            if not existing:
                session.add(user)
                print(f"Added user: {user.email}")
            else:
                print(f"User already exists: {user.email}")
        
        session.commit()

        print("Initializing daily participation...")
        initialize_daily_participation(date.today())
        
        print("Seeding complete!")

if __name__ == "__main__":
    seed_data()
