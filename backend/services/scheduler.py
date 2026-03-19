"""
Scheduler Service
Handles task scheduling with APScheduler
"""
import logging
from datetime import datetime
from typing import Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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

    print("\n" + "="*60)
    print("[调度器] 正在初始化调度器...")
    print("="*60)

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
        from apscheduler.triggers.interval import IntervalTrigger
        from apscheduler.triggers.date import DateTrigger

        scheduler = BackgroundScheduler(timezone='Asia/Shanghai')
        scheduler.start()

        print("[调度器] 调度器启动成功!")
        logger.info("Scheduler initialized successfully")

        # Load existing active schedules
        with app.app_context():
            from models import Schedule
            schedules = Schedule.query.filter_by(is_active=True).all()
            print(f"[调度器] 发现 {len(schedules)} 个活跃的调度任务")

            for schedule in schedules:
                try:
                    add_schedule_job(schedule)
                except Exception as e:
                    logger.error(f"Failed to load schedule {schedule.id}: {e}")
                    print(f"[调度器] 加载调度 {schedule.id} 失败: {e}")

        # 打印当前所有任务
        print_scheduler_jobs()

    except Exception as e:
        logger.error(f"Failed to initialize scheduler: {e}")
        print(f"[调度器] 初始化失败: {e}")


def print_scheduler_jobs():
    """打印当前所有调度任务"""
    global scheduler
    if not scheduler:
        print("[调度器] 调度器未初始化")
        return

    jobs = scheduler.get_jobs()
    print(f"\n[调度器] 当前共有 {len(jobs)} 个调度任务:")
    print("-"*60)
    for job in jobs:
        print(f"  - ID: {job.id}")
        print(f"    下次执行: {job.next_run_time}")
        print(f"    触发器: {job.trigger}")
    print("-"*60 + "\n")


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
        print("[调度器] 警告: 调度器未初始化")
        return False

    try:
        job_id = f"schedule_{schedule.id}"
        config = schedule.get_schedule_config()

        print(f"\n[调度器] 添加调度任务: {job_id}")
        print(f"  - 调度名称: {schedule.name}")
        print(f"  - 调度类型: {schedule.schedule_type}")
        print(f"  - 配置: {config}")

        # Determine trigger
        if schedule.schedule_type == 'cron':
            from apscheduler.triggers.cron import CronTrigger
            cron_expr = config.get('cron_expression', '0 0 * * *')
            print(f"  - Cron表达式: {cron_expr}")
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
            print(f"  - 间隔秒数: {interval_seconds}")
            trigger = IntervalTrigger(seconds=interval_seconds)

        elif schedule.schedule_type == 'date':
            from apscheduler.triggers.date import DateTrigger
            run_time = config.get('run_time')
            print(f"  - 执行时间: {run_time}")
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
        print(f"[调度器] 成功添加调度任务: {job_id}")

        # 打印下次执行时间
        job = scheduler.get_job(job_id)
        if job:
            print(f"  - 下次执行时间: {job.next_run_time}")

        return True

    except Exception as e:
        logger.error(f"Failed to add schedule job: {e}")
        print(f"[调度器] 添加调度任务失败: {e}")
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
        print("[调度器] 警告: 调度器未初始化，无法移除任务")
        return False

    try:
        job_id = f"schedule_{schedule.id}"

        # 先检查任务是否存在
        existing_job = scheduler.get_job(job_id)
        if existing_job:
            scheduler.remove_job(job_id)
            logger.info(f"Removed schedule job: {job_id}")
            print(f"[调度器] 成功移除调度任务: {job_id}")
        else:
            print(f"[调度器] 任务 {job_id} 不存在于调度器中")

        return True

    except Exception as e:
        logger.error(f"Failed to remove schedule job: {e}")
        print(f"[调度器] 移除调度任务失败: {e}")
        return False


def update_schedule_job(schedule) -> bool:
    """
    Update a job in the scheduler

    Args:
        schedule: Schedule model instance

    Returns:
        bool: True if successful
    """
    print(f"[调度器] 更新调度任务: schedule_{schedule.id}, is_active={schedule.is_active}")
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
    print("\n" + "="*60)
    print(f"[调度触发] 开始执行调度任务 schedule_id={schedule_id}")
    print(f"[调度触发] 执行时间: {datetime.now().isoformat()}")
    print("="*60)

    from app import app, db
    from models import Schedule, TaskExecution, ELTTask, DataSource
    from services.elt_engine import ELTEngine

    with app.app_context():
        schedule = Schedule.query.get(schedule_id)
        if not schedule:
            logger.error(f"Schedule {schedule_id} not found")
            print(f"[调度触发] 错误: 调度 {schedule_id} 不存在")
            return

        # 检查调度是否仍然活跃
        if not schedule.is_active:
            print(f"[调度触发] 调度 {schedule_id} 已暂停，跳过执行")
            logger.info(f"Schedule {schedule_id} is not active, skipping execution")
            return

        task = ELTTask.query.get(schedule.task_id)
        if not task:
            logger.error(f"Task {schedule.task_id} not found")
            print(f"[调度触发] 错误: 任务 {schedule.task_id} 不存在")
            return

        print(f"[调度触发] 任务名称: {task.name}")
        print(f"[调度触发] 调度名称: {schedule.name}")

        # 获取源和目标数据源
        source_ds = DataSource.query.get(task.source_db_id)
        target_ds = DataSource.query.get(task.target_db_id)

        if not source_ds:
            logger.error(f"Source datasource {task.source_db_id} not found")
            print(f"[调度触发] 错误: 源数据源 {task.source_db_id} 不存在")
            return
        if not target_ds:
            logger.error(f"Target datasource {task.target_db_id} not found")
            print(f"[调度触发] 错误: 目标数据源 {task.target_db_id} 不存在")
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

        print(f"[调度触发] 创建执行记录: execution_id={execution.id}")

        retry_count = 0
        max_retries = schedule.retry_count

        while retry_count <= max_retries:
            try:
                print(f"[调度触发] 开始执行ELT任务 (重试次数: {retry_count}/{max_retries})")

                # Execute task
                engine = ELTEngine()
                result = engine.execute(task, source_ds, target_ds)

                # Success
                execution.status = 'success'
                execution.end_time = datetime.utcnow()
                execution.processed_rows = result.get('processed_rows', 0)
                execution.execution_log = result.get('log', '')
                db.session.commit()

                logger.info(f"Task {task.id} executed successfully")
                print(f"[调度触发] 任务执行成功! 处理行数: {execution.processed_rows}")
                break

            except Exception as e:
                retry_count += 1
                print(f"[调度触发] 任务执行失败: {e}")

                if retry_count > max_retries:
                    # All retries exhausted
                    execution.status = 'failed'
                    execution.end_time = datetime.utcnow()
                    execution.error_message = str(e)
                    db.session.commit()

                    logger.error(f"Task {task.id} failed after {max_retries} retries: {e}")
                    print(f"[调度触发] 任务最终失败，已重试 {max_retries} 次")
                else:
                    # Wait before retry
                    import time
                    print(f"[调度触发] 等待 {schedule.retry_interval} 秒后重试...")
                    time.sleep(schedule.retry_interval)
                    logger.warning(f"Task {task.id} failed, retry {retry_count}/{max_retries}")

    print("="*60 + "\n")


def get_scheduler_status():
    """获取调度器状态"""
    global scheduler
    if not scheduler:
        return {
            'initialized': False,
            'running': False,
            'jobs': []
        }

    from datetime import timezone
    try:
        from zoneinfo import ZoneInfo
        local_tz = ZoneInfo('Asia/Shanghai')
    except ImportError:
        import pytz
        local_tz = pytz.timezone('Asia/Shanghai')

    jobs = scheduler.get_jobs()
    result_jobs = []
    for job in jobs:
        next_run = job.next_run_time
        if next_run:
            # 转换为本地时间
            if next_run.tzinfo is None:
                next_run = next_run.replace(tzinfo=timezone.utc)
            local_next_run = next_run.astimezone(local_tz)
            next_run_str = local_next_run.strftime('%Y-%m-%d %H:%M:%S')
        else:
            next_run_str = None

        result_jobs.append({
            'id': job.id,
            'next_run_time': next_run_str,
            'trigger': str(job.trigger)
        })

    return {
        'initialized': True,
        'running': scheduler.running,
        'jobs': result_jobs
    }


# Export
__all__ = ['init_scheduler', 'add_schedule_job', 'remove_schedule_job', 'update_schedule_job', 'get_scheduler_status', 'print_scheduler_jobs']