"""
Schedule Routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Schedule, ELTTask
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)
schedules_bp = Blueprint('schedules', __name__)


def get_local_tz():
    """获取本地时区"""
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo('Asia/Shanghai')
    except ImportError:
        import pytz
        return pytz.timezone('Asia/Shanghai')


LOCAL_TZ = get_local_tz()


def format_datetime_local(dt: datetime) -> str:
    """将时间转换为本地时区的标准格式字符串"""
    if dt is None:
        return None

    try:
        # 如果是 naive datetime，假设是 UTC
        if dt.tzinfo is None:
            utc_tz = timezone.utc
            dt = dt.replace(tzinfo=utc_tz)

        # 转换为本地时区
        local_dt = dt.astimezone(LOCAL_TZ)

        # 返回标准格式字符串
        return local_dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        logger.error(f"Error formatting datetime: {e}")
        return str(dt) if dt else None


@schedules_bp.route('', methods=['GET'])
@jwt_required()
def get_schedules():
    user_id = int(get_jwt_identity())
    schedules = Schedule.query.filter_by(created_by=user_id).order_by(Schedule.created_at.desc()).all()

    # 获取任务名称映射
    task_ids = [s.task_id for s in schedules]
    tasks = {t.id: t.name for t in ELTTask.query.filter(ELTTask.id.in_(task_ids)).all()}

    result = []
    for s in schedules:
        item = s.to_dict()
        item['task_name'] = tasks.get(s.task_id, 'Unknown')
        item['created_at'] = format_datetime_local(s.created_at)

        # 计算下次执行时间
        if s.is_active:
            next_run = _calculate_next_run(s)
            item['next_run_time'] = format_datetime_local(next_run)
        else:
            item['next_run_time'] = None

        result.append(item)

    return jsonify(result), 200


def get_local_now():
    """获取当前本地时间"""
    try:
        return datetime.now(LOCAL_TZ)
    except:
        # pytz 方式
        return LOCAL_TZ.localize(datetime.now())


def _calculate_next_run(schedule):
    """计算下次执行时间（返回本地时区时间）"""
    config = schedule.get_schedule_config()

    try:
        if schedule.schedule_type == 'cron':
            # 解析 cron 表达式计算下次执行时间
            cron_expr = config.get('cron_expression', '').strip()
            if cron_expr:
                return _get_next_cron_time(cron_expr)
            return None

        elif schedule.schedule_type == 'interval':
            # 间隔执行 - 使用本地时间计算
            interval = config.get('interval_seconds', 3600)
            now_local = get_local_now()
            return now_local + timedelta(seconds=interval)

        elif schedule.schedule_type == 'date':
            # 指定时间执行
            run_time = config.get('run_time')
            if run_time:
                try:
                    dt = datetime.fromisoformat(run_time.replace('Z', '+00:00'))
                    return dt.astimezone(LOCAL_TZ)
                except:
                    return None
            return None

    except Exception as e:
        logger.error(f"Failed to calculate next run time: {e}")
        return None

    return None


def _get_next_cron_time(cron_expression):
    """
    解析 cron 表达式并计算下次执行时间
    cron 格式: minute hour day_of_month month day_of_week
    例如: "0 2 * * *" 表示每天凌晨2点执行

    返回本地时区时间
    """
    try:
        parts = cron_expression.split()
        if len(parts) != 5:
            return None

        minute, hour, day_of_month, month, day_of_week = parts

        # 使用本地时间计算
        now_local = get_local_now()

        # 解析目标时间
        target_hour = int(hour) if hour != '*' else 0
        target_minute = int(minute) if minute != '*' else 0

        # 构建今天的目标时间（本地时区）
        target = now_local.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)

        # 如果目标时间已过，设置为明天
        if target <= now_local:
            target += timedelta(days=1)

        return target

    except Exception as e:
        logger.error(f"Failed to parse cron expression '{cron_expression}': {e}")
        return None


@schedules_bp.route('/<int:schedule_id>', methods=['GET'])
@jwt_required()
def get_schedule(schedule_id):
    """获取单个调度详情"""
    user_id = int(get_jwt_identity())
    schedule = Schedule.query.filter_by(id=schedule_id, created_by=user_id).first()
    if not schedule:
        return jsonify({'error': 'Not found'}), 404

    item = schedule.to_dict()
    task = ELTTask.query.get(schedule.task_id)
    item['task_name'] = task.name if task else 'Unknown'
    item['created_at'] = format_datetime_local(schedule.created_at)

    # 计算下次执行时间
    if schedule.is_active:
        next_run = _calculate_next_run(schedule)
        item['next_run_time'] = format_datetime_local(next_run)
    else:
        item['next_run_time'] = None

    return jsonify(item), 200


@schedules_bp.route('', methods=['POST'])
@jwt_required()
def create_schedule():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    print(f"\n[创建调度] 接收数据: {data}")

    if not data or not data.get('name') or not data.get('task_id') or not data.get('schedule_type'):
        return jsonify({'error': 'Missing required fields'}), 400

    # 验证任务是否存在
    task = ELTTask.query.filter_by(id=data['task_id'], created_by=user_id).first()
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    schedule = Schedule(
        task_id=data['task_id'],
        name=data['name'],
        schedule_type=data['schedule_type'],
        retry_count=data.get('retry_count', 0),
        retry_interval=data.get('retry_interval', 300),
        is_active=data.get('is_active', True),
        created_by=user_id
    )
    schedule.set_schedule_config(data.get('schedule_config', {}))
    if data.get('dependencies'):
        schedule.set_dependencies(data['dependencies'])

    db.session.add(schedule)
    db.session.commit()

    print(f"[创建调度] 调度创建成功: id={schedule.id}, name={schedule.name}, is_active={schedule.is_active}")

    # 添加到调度器
    if schedule.is_active:
        from services.scheduler import add_schedule_job, print_scheduler_jobs
        add_schedule_job(schedule)
        print_scheduler_jobs()

    return jsonify({'message': 'Created', 'schedule': schedule.to_dict()}), 201


@schedules_bp.route('/<int:schedule_id>', methods=['PUT'])
@jwt_required()
def update_schedule(schedule_id):
    user_id = int(get_jwt_identity())
    schedule = Schedule.query.filter_by(id=schedule_id, created_by=user_id).first()
    if not schedule:
        return jsonify({'error': 'Not found'}), 404

    data = request.get_json()
    print(f"\n[更新调度] 调度ID: {schedule_id}, 数据: {data}")

    for field in ['name', 'schedule_type', 'retry_count', 'retry_interval', 'is_active']:
        if data.get(field) is not None:
            setattr(schedule, field, data[field])

    if data.get('schedule_config'):
        schedule.set_schedule_config(data['schedule_config'])

    db.session.commit()

    print(f"[更新调度] 更新后: is_active={schedule.is_active}")

    # 更新调度器
    from services.scheduler import update_schedule_job, print_scheduler_jobs
    update_schedule_job(schedule)
    print_scheduler_jobs()

    return jsonify({'message': 'Updated', 'schedule': schedule.to_dict()}), 200


@schedules_bp.route('/<int:schedule_id>', methods=['DELETE'])
@jwt_required()
def delete_schedule(schedule_id):
    user_id = int(get_jwt_identity())
    schedule = Schedule.query.filter_by(id=schedule_id, created_by=user_id).first()
    if not schedule:
        return jsonify({'error': 'Not found'}), 404

    print(f"\n[删除调度] 调度ID: {schedule_id}")

    # 从调度器移除
    from services.scheduler import remove_schedule_job, print_scheduler_jobs
    remove_schedule_job(schedule)
    print_scheduler_jobs()

    db.session.delete(schedule)
    db.session.commit()

    return jsonify({'message': 'Deleted'}), 200


@schedules_bp.route('/<int:schedule_id>/toggle', methods=['POST'])
@jwt_required()
def toggle_schedule(schedule_id):
    user_id = int(get_jwt_identity())
    schedule = Schedule.query.filter_by(id=schedule_id, created_by=user_id).first()
    if not schedule:
        return jsonify({'error': 'Not found'}), 404

    schedule.is_active = not schedule.is_active
    db.session.commit()

    print(f"\n[切换调度] 调度ID: {schedule_id}, 新状态: is_active={schedule.is_active}")

    # 更新调度器
    from services.scheduler import update_schedule_job, print_scheduler_jobs
    update_schedule_job(schedule)
    print_scheduler_jobs()

    return jsonify({'message': 'Toggled', 'schedule': schedule.to_dict()}), 200


@schedules_bp.route('/status', methods=['GET'])
@jwt_required()
def get_scheduler_status():
    """获取调度器状态"""
    from services.scheduler import get_scheduler_status
    status = get_scheduler_status()
    return jsonify(status), 200