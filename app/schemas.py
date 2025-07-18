from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

# ===================
# Project Context
# ===================
class ProjectContextBase(BaseModel):
    key: str
    value: Optional[str] = None

class ProjectContextCreate(ProjectContextBase):
    pass

class ProjectContext(ProjectContextBase):
    updated_at: datetime

    class Config:
        from_attributes = True

# ===================
# Journal
# ===================
class JournalBase(BaseModel):
    task_id: str
    event_type: str

class JournalCreate(JournalBase):
    pass

class Journal(JournalBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

# ===================
# Task
# ===================
class TaskBase(BaseModel):
    task_id: str
    description: str
    details: Optional[str] = None
    type: str
    status: str = 'PENDING'
    dependencies: Optional[List[str]] = [] # Handled as a JSON string in DB, but list in API
    assignee_role: Optional[str] = None

class TaskCreate(TaskBase):
    pass

class Task(TaskBase):
    created_at: datetime
    updated_at: datetime
    journal_entries: List[Journal] = []

    class Config:
        from_attributes = True

# For tools: startWorkOnTask, finishWorkOnTask, getTaskDetails
class TaskIdPayload(BaseModel):
    task_id: str

# ===================
# MCP Tool Schemas
# ===================

# For tool: createTaskChain
class TaskChainCreate(BaseModel):
    tasks: List[TaskCreate]

# For tool: getNextReadyTask
class NextReadyTask(BaseModel):
    task_id: str
    type: str
    assignee_role: Optional[str] = None

# For tool: getInconsistentTasks
class InconsistentTask(BaseModel):
    task_id: str
    last_event: str

class InconsistentTaskList(BaseModel):
    inconsistent_tasks: List[InconsistentTask]

# For tool: updateTaskStatus
class TaskStatusUpdate(BaseModel):
    task_id: str
    status: str
    context_message: Optional[str] = None

# For tool: updateSystemPatterns
class SystemPatternsUpdate(BaseModel):
    patterns: str

# For tool: getSystemPatterns
class SystemPatterns(BaseModel):
    patterns: str

# For tool: getActiveContext / appendActiveContext
class ActiveContext(BaseModel):
    context: str