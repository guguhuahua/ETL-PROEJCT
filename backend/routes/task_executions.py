"""
Task Execution Routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, TaskExecution, ELTTask

task_executions_bp = Blueprint('task_executions', __name__)


@task_executions_bp.route('', methods=['GET'])
@jwt_required()
def get_executions():
    user_id = int(get_jwt_identity())
    task_id = request.args.get('task_id', type=int)
    per_page = request.args.get('per_page', 10, type=int)
    page = request.args.get('page', 1, type=int)

    # 获取用户的任务ID列表
    user_task_ids = [t.id for t in ELTTask.query.filter_by(created_by=user_id).all()]

    if not user_task_ids:
        return jsonify({'executions': [], 'total': 0, 'pages': 1, 'current_page': 1}), 200

    # 构建查询
    query = TaskExecution.query.filter(TaskExecution.task_id.in_(user_task_ids))

    if task_id:
        query = query.filter(TaskExecution.task_id == task_id)

    # 分页
    total = query.count()
    executions = query.order_by(TaskExecution.start_time.desc()).offset((page - 1) * per_page).limit(per_page).all()

    # 获取任务名称
    task_names = {t.id: t.name for t in ELTTask.query.filter(ELTTask.id.in_(user_task_ids)).all()}

    result = []
    for e in executions:
        item = e.to_dict()
        item['task_name'] = task_names.get(e.task_id, 'Unknown')
        result.append(item)

    return jsonify({
        'executions': result,
        'total': total,
        'pages': (total + per_page - 1) // per_page,
        'current_page': page
    }), 200


@task_executions_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    user_id = int(get_jwt_identity())
    user_task_ids = [t.id for t in ELTTask.query.filter_by(created_by=user_id).all()]

    if not user_task_ids:
        return jsonify({
            'total_executions': 0,
            'success_count': 0,
            'failed_count': 0,
            'running_count': 0,
            'total_processed_rows': 0
        }), 200

    total = TaskExecution.query.filter(TaskExecution.task_id.in_(user_task_ids)).count()
    success = TaskExecution.query.filter(
        TaskExecution.task_id.in_(user_task_ids),
        TaskExecution.status == 'success'
    ).count()
    failed = TaskExecution.query.filter(
        TaskExecution.task_id.in_(user_task_ids),
        TaskExecution.status == 'failed'
    ).count()
    running = TaskExecution.query.filter(
        TaskExecution.task_id.in_(user_task_ids),
        TaskExecution.status == 'running'
    ).count()

    # 计算总处理行数
    from sqlalchemy import func
    total_rows = db.session.query(func.sum(TaskExecution.processed_rows)).filter(
        TaskExecution.task_id.in_(user_task_ids)
    ).scalar() or 0

    return jsonify({
        'total_executions': total,
        'success_count': success,
        'failed_count': failed,
        'running_count': running,
        'total_processed_rows': total_rows
    }), 200


@task_executions_bp.route('/<int:execution_id>', methods=['GET'])
@jwt_required()
def get_execution(execution_id):
    user_id = int(get_jwt_identity())
    user_task_ids = [t.id for t in ELTTask.query.filter_by(created_by=user_id).all()]

    execution = TaskExecution.query.filter(
        TaskExecution.id == execution_id,
        TaskExecution.task_id.in_(user_task_ids)
    ).first()

    if not execution:
        return jsonify({'error': 'Not found'}), 404

    result = execution.to_dict()
    task = ELTTask.query.get(execution.task_id)
    result['task_name'] = task.name if task else 'Unknown'

    return jsonify(result), 200