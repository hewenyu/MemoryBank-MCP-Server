import json
from sqlalchemy.orm import Session
from . import models, schemas

# ===================
# Task CRUD
# ===================

def get_task(db: Session, task_id: str):
    return db.query(models.Task).filter(models.Task.task_id == task_id).first()

def get_tasks(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Task).offset(skip).limit(limit).all()

def create_task(db: Session, task: schemas.TaskCreate):
    # Pydantic model has a list of strings, but DB model stores a JSON string.
    dependencies_json = json.dumps(task.dependencies)
    db_task = models.Task(
        **task.model_dump(exclude={'dependencies'}),
        dependencies=dependencies_json
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def get_next_ready_task(db: Session):
    """
    Finds the next task that is 'PENDING' and has all its dependencies 'COMPLETED'.
    """
    pending_tasks = db.query(models.Task).filter(models.Task.status == 'PENDING').order_by(models.Task.created_at).all()
    
    for task in pending_tasks:
        if not task.dependencies or task.dependencies == '[]':
            return task # No dependencies, ready to run

        try:
            dependency_ids = json.loads(task.dependencies)
        except json.JSONDecodeError:
            continue # Skip if dependencies are malformed

        if not dependency_ids:
            return task # Empty dependency list

        # Check status of all dependent tasks
        dependencies_met = True
        for dep_id in dependency_ids:
            dep_task = get_task(db, dep_id)
            if not dep_task or dep_task.status != 'COMPLETED':
                dependencies_met = False
                break
        
        if dependencies_met:
            return task
            
    return None

# ===================
# Journal CRUD
# ===================

def create_journal_entry(db: Session, entry: schemas.JournalCreate):
    db_entry = models.Journal(**entry.model_dump())
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry

# ===================
# Project Context CRUD
# ===================

def get_project_context(db: Session, key: str):
    return db.query(models.ProjectContext).filter(models.ProjectContext.key == key).first()

def create_or_update_project_context(db: Session, context: schemas.ProjectContextCreate):
    db_context = get_project_context(db, context.key)
    if db_context:
        db_context.value = context.value
    else:
        db_context = models.ProjectContext(**context.model_dump())
        db.add(db_context)
    db.commit()
    db.refresh(db_context)
    return db_context

def append_project_context(db: Session, key: str, content_to_append: str):
    db_context = get_project_context(db, key)
    if db_context:
        if db_context.value:
            db_context.value += "\n" + content_to_append
        else:
            db_context.value = content_to_append
    else:
        # If key does not exist, create it.
        db_context = models.ProjectContext(key=key, value=content_to_append)
        db.add(db_context)
    db.commit()
    db.refresh(db_context)
    return db_context