from sqlmodel import SQLModel, create_engine, Session
from pathlib import Path

sqlite_file_name = "database.db"
base_dir = Path(__file__).parent.parent
data_dir = base_dir / "data"
data_dir.mkdir(exist_ok=True)
sqlite_url = f"sqlite:///{data_dir / sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=False, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
