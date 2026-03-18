"""
Scheduler Service
Handles task scheduling with APScheduler
"""
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


def init_scheduler(app):
    """
    Initialize the scheduler

    Args:
        app: Flask application instance
    """
    global scheduler

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
        from apscheduler.triggers.interval import IntervalTrigger
        from apscheduler.triggers.date import DateTrigger

        scheduler = BackgroundScheduler(timezone='Asia/Shanghai')
        scheduler.start()

        logger.info("Scheduler initialized successfully")

        # Load existing active schedules
        with app.app_context():
            from models.schedule import Schedule
            schedules = Schedule.query.filter_by(is_active=True).all()
            for schedule in schedules:
                try:
                    add_schedule_job(schedule)
                except Exception as e:
                    logger.error(f"Failed to load schedule {schedule.id}: {e}")

    except Exception as e:
        logger.error(f"Failed to initialize scheduler: {e}")


def add_schedule_job(schedule) -> bool:
    """
    Add a job to the scheduler

    Args:
        schedule: Schedule model instance

    Returns:
        bool: True if successful
    """
    global scheduler

    if not scheduler:
        logger.warning("Scheduler not initialized")
        return False

    try:
        job_id = f"schedule_{schedule.id}"
        config = schedule.get_schedule_config()

        # Determine trigger
        if schedule.schedule_type == 'cron':
            from apscheduler.triggers.cron import CronTrigger
            cron_expr = config.get('cron_expression', '0 0 * * *')
            # Parse cron expression (simplified)
            parts = cron_expr.split()
            if len(parts) >= 5:
                trigger = CronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4]
                )
            else:
                raise ValueError("Invalid cron expression")

        elif schedule.schedule_type == 'interval':
            from apscheduler.triggers.interval import IntervalTrigger
            interval_seconds = config.get('interval_seconds', 3600)
            trigger = IntervalTrigger(seconds=interval_seconds)

        elif schedule.schedule_type == 'date':
            from apscheduler.triggers.date import DateTrigger
            run_time = config.get('run_time')
            if run_time:
                trigger = DateTrigger(run_date=run_time)
            else:
                raise ValueError("Run time required for date schedule")

        else:
            raise ValueError(f"Unknown schedule type: {schedule.schedule_type}")

        # Add job
        scheduler.add_job(
            func=execute_scheduled_task,
            trigger=trigger,
            id=job_id,
            args=[schedule.id],
            replace_existing=True
        )

        logger.info(f"Added schedule job: {job_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to add schedule job: {e}")
        return False


def remove_schedule_job(schedule) -> bool:
    """
    Remove a job from the scheduler

    Args:
        schedule: Schedule model instance

    Returns:
        bool: True if successful
    """
    global scheduler

    if not scheduler:
        return False

    try:
        job_id = f"schedule_{schedule.id}"
        scheduler.remove_job(job_id)
        logger.info(f"Removed schedule job: {job_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to remove schedule job: {e}")
        return False


def update_schedule_job(schedule) -> bool:
    """
    Update a job in the scheduler

    Args:
        schedule: Schedule model instance

    Returns:
        bool: True if successful
    """
    # Remove existing job
    remove_schedule_job(schedule)

    # Add new job if active
    if schedule.is_active:
        return add_schedule_job(schedule)

    return True


def execute_scheduled_task(schedule_id: int):
    """
    Execute a scheduled task

    Args:
        schedule_id: Schedule ID
    """
    from app import app, db
    from models.schedule import Schedule
    from models.task_execution import TaskExecution
    from models.elt_task import ELTTask
    from services.elt_engine import ELTEngine

    with app.app_context():
        schedule = Schedule.query.get(schedule_id)
        if not schedule:
            logger.error(f"Schedule {schedule_id} not found")
            return

        task = ELTTask.query.get(schedule.task_id)
        if not task:
            logger.error(f"Task {schedule.task_id} not found")
            return

        # Create execution record
        execution = TaskExecution(
            task_id=task.id,
            schedule_id=schedule.id,
            status='running',
            start_time=datetime.utcnow()
        )
        db.session.add(execution)
        db.session.commit()

        retry_count = 0
        max_retries = schedule.retry_count

        while retry_count <= max_retries:
            try:
                # Execute task
                engine = ELTEngine()
                result = engine.execute(task)

                # Success
                execution.status = 'success'
                execution.end_time = datetime.utcnow()
                execution.processed_rows = result.get('processed_rows', 0)
                execution.execution_log = result.get('log', '')
                db.session.commit()

                logger.info(f"Task {task.id} executed successfully")
                break

            except Exception as e:
                retry_count += 1

                if retry_count > max_retries:
                    # All retries exhausted
                    execution.status = 'failed'
                    execution.end_time = datetime.utcnow()
                    execution.error_message = str(e)
                    db.session.commit()

                    logger.error(f"Task {task.id} failed after {max_retries} retries: {e}")
                else:
                    # Wait before retry
                    import time
                    time.sleep(schedule.retry_interval)
                    logger.warning(f"Task {task.id} failed, retry {retry_count}/{max_retries}")


# Export
__all__ = ['init_scheduler', 'add_schedule_job', 'remove_schedule_job', 'update_schedule_job']