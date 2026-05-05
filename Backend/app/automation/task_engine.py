# backend/app/automation/task_engine.py
"""
Task Automation Engine - To-Do Management, Scheduling, Reminders
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from enum import Enum
from sqlalchemy import create_engine, Column, String, Text, DateTime, Boolean, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
import json
from apscheduler.schedulers.background import BackgroundScheduler

Base = declarative_base()


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"


class Task(Base):
    """Task model for to-do management"""
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, index=True)
    title = Column(String)
    description = Column(Text)
    status = Column(String, default=TaskStatus.PENDING.value)
    priority = Column(Integer, default=3)  # 1=high, 2=medium, 3=low
    due_date = Column(DateTime, nullable=True)
    reminder_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    meta_data = Column(Text, default="{}")  # JSON for tags, subtasks, etc.


class Schedule(Base):
    """Recurring task schedule"""
    __tablename__ = "schedules"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, index=True)
    task_template = Column(Text)  # JSON template for recurring task
    frequency = Column(String)  # "daily", "weekly", "monthly"
    next_occurrence = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Reminder(Base):
    """Reminders for tasks"""
    __tablename__ = "reminders"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, index=True)
    task_id = Column(String)
    message = Column(Text)
    trigger_time = Column(DateTime)
    sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class TaskEngine:
    """Manages tasks, scheduling, and reminders"""
    
    def __init__(self, db_url: str = "sqlite:///./omniai.db"):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Initialize scheduler
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
    
    # ============= TASK MANAGEMENT =============
    def create_task(self, user_id: str, title: str, description: str = "",
                   priority: int = 3, due_date: Optional[DateTime] = None) -> Dict:
        """Create a new task"""
        from uuid import uuid4
        session = self.SessionLocal()
        try:
            task = Task(
                id=str(uuid4()),
                user_id=user_id,
                title=title,
                description=description,
                priority=priority,
                due_date=due_date
            )
            session.add(task)
            session.commit()
            
            return {
                "id": task.id,
                "title": task.title,
                "status": task.status,
                "created_at": task.created_at.isoformat()
            }
        finally:
            session.close()
    
    def get_tasks(self, user_id: str, status: Optional[str] = None, 
                  sort_by: str = "due_date") -> List[Dict]:
        """Get user's tasks"""
        session = self.SessionLocal()
        try:
            query = session.query(Task).filter(Task.user_id == user_id)
            
            if status:
                query = query.filter(Task.status == status)
            
            # Sort by due date or priority
            if sort_by == "priority":
                query = query.order_by(Task.priority.asc())
            else:
                query = query.order_by(Task.due_date.asc())
            
            tasks = query.all()
            
            return [{
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "status": t.status,
                "priority": t.priority,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "meta_data": json.loads(t.meta_data)
            } for t in tasks]
        finally:
            session.close()
    
    def update_task(self, task_id: str, **updates) -> Dict:
        """Update task"""
        session = self.SessionLocal()
        try:
            task = session.query(Task).filter(Task.id == task_id).first()
            if not task:
                return {"error": "Task not found"}
            
            for key, value in updates.items():
                if key == "status" and value == TaskStatus.COMPLETED.value:
                    task.completed_at = datetime.utcnow()
                setattr(task, key, value)
            
            task.updated_at = datetime.utcnow()
            session.commit()
            
            return {"status": "updated", "task_id": task_id}
        finally:
            session.close()
    
    def delete_task(self, task_id: str) -> Dict:
        """Delete task"""
        session = self.SessionLocal()
        try:
            task = session.query(Task).filter(Task.id == task_id).first()
            if not task:
                return {"error": "Task not found"}
            
            session.delete(task)
            session.commit()
            return {"status": "deleted"}
        finally:
            session.close()
    
    # ============= SCHEDULING =============
    def create_recurring_task(self, user_id: str, task_template: Dict,
                             frequency: str = "daily") -> Dict:
        """Create recurring task (daily/weekly/monthly)"""
        from uuid import uuid4
        session = self.SessionLocal()
        try:
            schedule = Schedule(
                id=str(uuid4()),
                user_id=user_id,
                task_template=json.dumps(task_template),
                frequency=frequency,
                next_occurrence=datetime.utcnow() + self._get_next_occurrence(frequency)
            )
            session.add(schedule)
            session.commit()
            
            return {"id": schedule.id, "frequency": frequency}
        finally:
            session.close()
    
    def _get_next_occurrence(self, frequency: str) -> timedelta:
        """Calculate next occurrence based on frequency"""
        if frequency == "daily":
            return timedelta(days=1)
        elif frequency == "weekly":
            return timedelta(weeks=1)
        elif frequency == "monthly":
            return timedelta(days=30)
        return timedelta(days=1)
    
    def process_recurring_tasks(self) -> List[str]:
        """Process due recurring tasks"""
        session = self.SessionLocal()
        created_tasks = []
        try:
            schedules = session.query(Schedule)\
                .filter(Schedule.is_active == True)\
                .filter(Schedule.next_occurrence <= datetime.utcnow())\
                .all()
            
            for schedule in schedules:
                template = json.loads(schedule.task_template)
                
                # Create new task
                new_task = self.create_task(
                    user_id=schedule.user_id,
                    title=template.get("title"),
                    description=template.get("description"),
                    priority=template.get("priority", 3)
                )
                created_tasks.append(new_task["id"])
                
                # Update schedule
                schedule.next_occurrence = datetime.utcnow() + \
                    self._get_next_occurrence(schedule.frequency)
            
            session.commit()
        finally:
            session.close()
        
        return created_tasks
    
    # ============= REMINDERS =============
    def set_reminder(self, user_id: str, task_id: str, message: str,
                    trigger_time: datetime) -> Dict:
        """Set reminder for task"""
        from uuid import uuid4
        session = self.SessionLocal()
        try:
            reminder = Reminder(
                id=str(uuid4()),
                user_id=user_id,
                task_id=task_id,
                message=message,
                trigger_time=trigger_time
            )
            session.add(reminder)
            session.commit()
            
            return {"id": reminder.id, "scheduled_for": trigger_time.isoformat()}
        finally:
            session.close()
    
    def get_pending_reminders(self, user_id: str) -> List[Dict]:
        """Get reminders that need to be sent"""
        session = self.SessionLocal()
        try:
            reminders = session.query(Reminder)\
                .filter(Reminder.user_id == user_id)\
                .filter(Reminder.sent == False)\
                .filter(Reminder.trigger_time <= datetime.utcnow())\
                .all()
            
            return [{
                "id": r.id,
                "task_id": r.task_id,
                "message": r.message,
                "trigger_time": r.trigger_time.isoformat()
            } for r in reminders]
        finally:
            session.close()
    
    def mark_reminder_sent(self, reminder_id: str) -> Dict:
        """Mark reminder as sent"""
        session = self.SessionLocal()
        try:
            reminder = session.query(Reminder).filter(Reminder.id == reminder_id).first()
            if reminder:
                reminder.sent = True
                session.commit()
            return {"status": "marked_sent"}
        finally:
            session.close()
