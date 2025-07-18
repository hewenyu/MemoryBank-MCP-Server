from sqlalchemy.orm import Session
from . import models, schemas, crud
import json

def start_work_on_task(db: Session, task_id: str):
    """
    Atomically:
    1. Update task status to 'RUNNING'.
    2. Create a 'STARTING' journal entry.
    """
    try:
        # 1. Find the task
        db_task = crud.get_task(db, task_id=task_id)
        if not db_task:
            return None # Or raise an exception

        # 2. Update status
        db_task.status = 'RUNNING'

        # 3. Create journal entry
        journal_entry = schemas.JournalCreate(task_id=task_id, event_type='STARTING')
        db_journal_entry = models.Journal(**journal_entry.model_dump())
        
        db.add(db_task)
        db.add(db_journal_entry)
        
        db.commit()
        db.refresh(db_task)
        return db_task
    except Exception as e:
        db.rollback()
        raise e

def update_task_status(db: Session, task_id: str, status: str, context_message: str = None):
    """
    Atomically:
    1. Update task status.
    2. If context_message is provided, append it to the 'active_context'.
    """
    try:
        db_task = crud.get_task(db, task_id=task_id)
        if not db_task:
            return None

        db_task.status = status
        db.add(db_task)

        if context_message:
            crud.append_project_context(
                db=db,
                key="active_context",
                content_to_append=f"Context for task {task_id} (status: {status}): {context_message}"
            )
        
        db.commit()
        db.refresh(db_task)
        return db_task
    except Exception as e:
        db.rollback()
        raise e

def finish_work_on_task(db: Session, task_id: str):
    """
    Atomically:
    1. Update task status to 'COMPLETED'.
    2. Create a 'FINISHED' journal entry.
    """
    try:
        # 1. Find the task
        db_task = crud.get_task(db, task_id=task_id)
        if not db_task:
            return None # Or raise an exception

        # 2. Update status
        db_task.status = 'COMPLETED'

        # 3. Create journal entry
        journal_entry = schemas.JournalCreate(task_id=task_id, event_type='FINISHED')
        db_journal_entry = models.Journal(**journal_entry.model_dump())
        
        db.add(db_task)
        db.add(db_journal_entry)
        
        db.commit()
        db.refresh(db_task)
        return db_task
    except Exception as e:
        db.rollback()
        raise e