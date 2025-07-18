import json
from fastapi import FastAPI, Depends, HTTPException
from fastapi_mcp.server import FastApiMCP
from sqlalchemy.orm import Session
from typing import List, Optional

from . import crud, models, schemas, services
from .database import SessionLocal, engine

# Create all database tables based on the models
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MemoryBank-MCP-Server",
    description="A centralized, transactional context management service for AI agents.",
    version="0.1.0",
)

# Initialize FastAPI MCP server
mcp = FastApiMCP(app)

# Dependency to get a DB session for each request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==============================================================================
# MCP TOOLS IMPLEMENTATION (API ENDPOINTS)
# ==============================================================================

# -------------------
# Orchestrator-Architect Tools
# -------------------

@app.post("/tools/createTaskChain", response_model=List[schemas.Task], tags=["Orchestrator-Architect Tools"], operation_id="createTaskChain")
def create_task_chain(payload: schemas.TaskChainCreate, db: Session = Depends(get_db)):
    """
    Creates one or more tasks with dependencies in a single transaction.
    """
    created_tasks = []
    # Although crud.create_task commits one by one, for this initial version,
    # we will handle it this way. A more robust implementation might wrap this
    # entire loop in a single transaction in the service layer.
    for task_data in payload.tasks:
        # Check for duplicate task_id
        db_task = crud.get_task(db, task_id=task_data.task_id)
        if db_task:
            raise HTTPException(status_code=400, detail=f"Task with ID '{task_data.task_id}' already exists.")
        created_task = crud.create_task(db=db, task=task_data)
        created_tasks.append(created_task)

    # Parse dependencies from JSON string to list for the response model
    for task in created_tasks:
        if task.dependencies:
            try:
                task.dependencies = json.loads(task.dependencies)
            except json.JSONDecodeError:
                task.dependencies = [] # Handle malformed JSON
        else:
            task.dependencies = []
            
    return created_tasks

@app.post("/tools/getNextReadyTask", response_model=Optional[schemas.NextReadyTask], tags=["Orchestrator-Architect Tools"], operation_id="getNextReadyTask")
def get_next_ready_task(db: Session = Depends(get_db)):
    """
    Gets the next task that is PENDING and has all its dependencies COMPLETED.
    Returns null if no task is ready.
    """
    db_task = crud.get_next_ready_task(db)
    return db_task

# -------------------
# General Agent Tools
# -------------------

@app.post("/tools/getTaskDetails", response_model=schemas.Task, tags=["General Agent Tools"], operation_id="getTaskDetails")
def get_task_details(payload: schemas.TaskIdPayload, db: Session = Depends(get_db)):
    """
    Gets the full details for a specified task.
    """
    db_task = crud.get_task(db, task_id=payload.task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # The dependencies are stored as a JSON string, so we parse it back to a list
    # for the response model.
    if db_task.dependencies:
        try:
            db_task.dependencies = json.loads(db_task.dependencies)
        except json.JSONDecodeError:
            db_task.dependencies = [] # Handle malformed JSON
    else:
        db_task.dependencies = []
        
    return db_task

# -------------------
# Transactional Tools (for Developer)
# -------------------

@app.post("/tools/startWorkOnTask", response_model=schemas.Task, tags=["Transactional Tools"], operation_id="startWorkOnTask")
def start_work_on_task(payload: schemas.TaskIdPayload, db: Session = Depends(get_db)):
    """
    Atomically declares that work is starting on a task.
    - Updates task status to 'RUNNING'.
    - Creates a 'STARTING' journal entry.
    """
    task = services.start_work_on_task(db, task_id=payload.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.dependencies:
        try:
            task.dependencies = json.loads(task.dependencies)
        except json.JSONDecodeError:
            task.dependencies = []
    else:
        task.dependencies = []
    return task

@app.post("/tools/finishWorkOnTask", response_model=schemas.Task, tags=["Transactional Tools"], operation_id="finishWorkOnTask")
def finish_work_on_task(payload: schemas.TaskIdPayload, db: Session = Depends(get_db)):
    """
    Atomically declares that work is finished on a task.
    - Updates task status to 'COMPLETED'.
    - Creates a 'FINISHED' journal entry.
    """
    task = services.finish_work_on_task(db, task_id=payload.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.dependencies:
        try:
            task.dependencies = json.loads(task.dependencies)
        except json.JSONDecodeError:
            task.dependencies = []
    else:
        task.dependencies = []
    return task

# -------------------
# Context Tools (for Guardian/Developer)
# -------------------

@app.post("/tools/getSystemPatterns", response_model=schemas.SystemPatterns, tags=["Context Tools"], operation_id="getSystemPatterns")
def get_system_patterns(db: Session = Depends(get_db)):
    """
    Gets the system coding patterns.
    """
    context = crud.get_project_context(db, key="system_patterns")
    if not context or not context.value:
        return schemas.SystemPatterns(patterns="")
    return schemas.SystemPatterns(patterns=context.value)

@app.post("/tools/getActiveContext", response_model=schemas.ActiveContext, tags=["Context Tools"], operation_id="getActiveContext")
def get_active_context(db: Session = Depends(get_db)):
    """
    Gets the active context, such as failure reports.
    """
    context = crud.get_project_context(db, key="active_context")
    if not context or not context.value:
        return schemas.ActiveContext(context="")
    return schemas.ActiveContext(context=context.value)

@app.post("/tools/updateTaskStatus", response_model=schemas.Task, tags=["General Agent Tools"], operation_id="updateTaskStatus")
def update_task_status(payload: schemas.TaskStatusUpdate, db: Session = Depends(get_db)):
    """
    Updates the status of a task.
    If a context_message is provided, it's appended to the active_context.
    """
    task = services.update_task_status(
        db,
        task_id=payload.task_id,
        status=payload.status,
        context_message=payload.context_message
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.dependencies:
        try:
            task.dependencies = json.loads(task.dependencies)
        except json.JSONDecodeError:
            task.dependencies = []
    else:
        task.dependencies = []
    return task

@app.post("/tools/updateSystemPatterns", response_model=schemas.ProjectContext, tags=["Context Tools"], operation_id="updateSystemPatterns")
def update_system_patterns(payload: schemas.SystemPatternsUpdate, db: Session = Depends(get_db)):
    """
    Updates or creates the system coding patterns.
    """
    context_to_update = schemas.ProjectContextCreate(key="system_patterns", value=payload.patterns)
    return crud.create_or_update_project_context(db=db, context=context_to_update)

@app.post("/tools/appendActiveContext", response_model=schemas.ProjectContext, tags=["Context Tools"], operation_id="appendActiveContext")
def append_active_context(payload: schemas.ActiveContext, db: Session = Depends(get_db)):
    """
    Appends a message to the active context.
    """
    return crud.append_project_context(db=db, key="active_context", content_to_append=payload.context)

# Setup MCP server after all endpoints are defined
mcp.setup_server()

# Mount MCP endpoints to the main app
mcp.mount()