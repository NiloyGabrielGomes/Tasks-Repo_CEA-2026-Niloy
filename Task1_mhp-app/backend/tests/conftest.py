"""
Shared pytest fixtures.

Creates an in-memory SQLite database before each test function and tears it
down afterwards, so every test starts from a clean slate without touching the
real `data/database.db` file.
"""

import pytest
from sqlmodel import create_engine, SQLModel
from sqlmodel.pool import StaticPool


@pytest.fixture(autouse=True)
def test_db(monkeypatch):
    """
    Replace the production SQLite engine with an isolated in-memory engine
    for the duration of each test.

    Both `app.database.engine` and `app.storage.engine` are patched because
    `storage.py` binds the engine name at import time
    (``from app.database import engine``), so we must patch the storage
    module's own reference as well.
    """
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    import app.database as db_module
    import app.storage as st_module

    monkeypatch.setattr(db_module, "engine", test_engine)
    monkeypatch.setattr(st_module, "engine", test_engine)

    # Create all tables
    SQLModel.metadata.create_all(test_engine)
    yield test_engine
    SQLModel.metadata.drop_all(test_engine)
