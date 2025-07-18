import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch

from app.main import app, get_db
from app.database import Base
from app.models import Task, Journal
from app.services import start_work_on_task

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the database tables for the test session
# This line is no longer needed here as the fixture will handle table creation.
# Base.metadata.create_all(bind=engine)

# Override the get_db dependency to use the test database
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="function")
def db_session():
    """
    Fixture to provide a clean database session for each test function.
    It creates all tables before the test and drops them afterwards.
    """
    Base.metadata.create_all(bind=engine)
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_start_work_on_task_success(db_session):
    # 1. Setup: Create a task
    initial_task = Task(task_id="TASK-001", description="Test task", type="TDD", status="PENDING")
    db_session.add(initial_task)
    db_session.commit()

    # 2. Action: Call the endpoint
    response = client.post("/tools/startWorkOnTask", json={"task_id": "TASK-001"})

    # 3. Assert: Check the response and database state
    assert response.status_code == 200
    
    task_in_db = db_session.query(Task).filter(Task.task_id == "TASK-001").one()
    assert task_in_db.status == "RUNNING"

    journal_entry = db_session.query(Journal).filter(Journal.task_id == "TASK-001").one()
    assert journal_entry.event_type == "STARTING"

def test_finish_work_on_task_success(db_session):
    # 1. Setup: Create a task that is 'RUNNING'
    initial_task = Task(task_id="TASK-002", description="Test task", type="CODE", status="RUNNING")
    db_session.add(initial_task)
    db_session.commit()

    # 2. Action: Call the endpoint
    response = client.post("/tools/finishWorkOnTask", json={"task_id": "TASK-002"})

    # 3. Assert: Check the response and database state
    assert response.status_code == 200
    
    task_in_db = db_session.query(Task).filter(Task.task_id == "TASK-002").one()
    assert task_in_db.status == "COMPLETED"

    journal_entry = db_session.query(Journal).filter(Journal.task_id == "TASK-002").one()
    assert journal_entry.event_type == "FINISHED"

def test_start_work_on_task_atomicity_on_failure(db_session):
    """
    Ensures that if the transaction fails, no changes are committed to the DB.
    """
    # 1. Setup: Create a task
    initial_task = Task(task_id="TASK-003", description="Test atomicity", type="QA", status="PENDING")
    db_session.add(initial_task)
    db_session.commit()

    # 2. Action: We unit-test the service function's atomicity directly.
    # We patch a lower-level function (`db.add`) to simulate a failure
    # mid-transaction.
    with patch.object(db_session, 'add', side_effect=[None, Exception("Simulated DB crash")]) as mock_add:
        with pytest.raises(Exception, match="Simulated DB crash"):
            # Call the service function directly
            start_work_on_task(db_session, task_id="TASK-003")

    # 3. Assert: Check that the database state has NOT changed
    # The service's exception handler should have rolled back the session.
    task_in_db = db_session.query(Task).filter(Task.task_id == "TASK-003").one()
    assert task_in_db.status == "PENDING" # Status should NOT have changed to 'RUNNING'

    journal_count = db_session.query(Journal).filter(Journal.task_id == "TASK-003").count()
    assert journal_count == 0 # NO journal entry should have been created