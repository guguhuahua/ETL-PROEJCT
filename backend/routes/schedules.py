"""
Schedule Routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Schedule, ELTTask
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
schedules_bp = Blueprint('schedules', __name__)


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
        item['created_at'] = s.created_at.isoformat() if s.created_at else None

        # 计算下次执行时间
        if s.is_active:
            next_run = _calculate_next_run(s)
            item['next_run_time'] = next_run.isoformat() if isinstance(next_run, datetime) else next_run
        else:
            item['next_run_time'] = None

        result.append(item)

    return jsonify(result), 200


def _calculate_next_run(schedule):
    """计算下次执行时间"""
    config = schedule.get_schedule_config()

    try:
        if schedule.schedule_type == 'cron':
            # 解析 cron 表达式计算下次执行时间
            cron_expr = config.get('cron_expression', '').strip()
            if cron_expr:
                return _get_next_cron_time(cron_expr)
            return None

        elif schedule.schedule_type == 'interval':
            # 间隔执行
            interval = config.get('interval_seconds', 3600)
            return datetime.utcnow() + timedelta(seconds=interval)

        elif schedule.schedule_type == 'date':
            # 指定时间执行
            run_time = config.get('run_time')
            if run_time:
                try:
                    return datetime.fromisoformat(run_time.replace('Z', '+00:00'))
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
    """
    try:
        parts = cron_expression.split()
        if len(parts) != 5:
            return None

        minute, hour, day_of_month, month, day_of_week = parts
        now = datetime.utcnow()

        # 简化处理：只解析常见模式
        # 默认设置为今天或明天的指定时间
        target_hour = int(hour) if hour != '*' else 0
        target_minute = int(minute) if minute != '*' else 0

        # 构建今天的目标时间
        target = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)

        # 如果目标时间已过，设置为明天
        if target <= now:
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
    item['created_at'] = schedule.created_at.isoformat() if schedule.created_at else None

    return jsonify(item), 200


@schedules_bp.route('', methods=['POST'])
@jwt_required()
def create_schedule():
    user_id = int(get_jwt_identity())
    data = request.get_json()

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
    return jsonify({'message': 'Created', 'schedule': schedule.to_dict()}), 201


@schedules_bp.route('/<int:schedule_id>', methods=['PUT'])
@jwt_required()
def update_schedule(schedule_id):
    user_id = int(get_jwt_identity())
    schedule = Schedule.query.filter_by(id=schedule_id, created_by=user_id).first()
    if not schedule:
        return jsonify({'error': 'Not found'}), 404

    data = request.get_json()
    for field in ['name', 'schedule_type', 'retry_count', 'retry_interval', 'is_active']:
        if data.get(field) is not None:
            setattr(schedule, field, data[field])

    if data.get('schedule_config'):
        schedule.set_schedule_config(data['schedule_config'])

    db.session.commit()
    return jsonify({'message': 'Updated', 'schedule': schedule.to_dict()}), 200


@schedules_bp.route('/<int:schedule_id>', methods=['DELETE'])
@jwt_required()
def delete_schedule(schedule_id):
    user_id = int(get_jwt_identity())
    schedule = Schedule.query.filter_by(id=schedule_id, created_by=user_id).first()
    if not schedule:
        return jsonify({'error': 'Not found'}), 404

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
    return jsonify({'message': 'Toggled', 'schedule': schedule.to_dict()}), 200