from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship
from .database import Base

class Task(Base):
    __tablename__ = "tasks"

    task_id = Column(String(255), primary_key=True, index=True)
    description = Column(Text, nullable=False)
    details = Column(Text)
    type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default='PENDING')
    dependencies = Column(Text)  # Storing as a JSON string, e.g., '["TASK-001"]'
    assignee_role = Column(String(100))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    journal_entries = relationship("Journal", back_populates="task")

class Journal(Base):
    __tablename__ = "journal"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(255), ForeignKey("tasks.task_id"), nullable=False)
    event_type = Column(String(50), nullable=False)  # e.g., 'STARTING', 'FINISHED'
    timestamp = Column(TIMESTAMP, server_default=func.now())

    task = relationship("Task", back_populates="journal_entries")

class ProjectContext(Base):
    __tablename__ = "project_context"

    key = Column(String(255), primary_key=True, index=True)
    value = Column(Text)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())