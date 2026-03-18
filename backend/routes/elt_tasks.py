"""
ELT Task Routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from models import db, ELTTask, TaskExecution, DataSource
from services.elt_engine import elt_engine
import logging

logger = logging.getLogger(__name__)
elt_tasks_bp = Blueprint('elt_tasks', __name__)


@elt_tasks_bp.route('', methods=['GET'])
@jwt_required()
def get_elt_tasks():
    user_id = int(get_jwt_identity())
    tasks = ELTTask.query.filter_by(created_by=user_id).order_by(ELTTask.created_at.desc()).all()

    # 获取数据源名称映射
    ds_ids = set()
    for t in tasks:
        ds_ids.add(t.source_db_id)
        ds_ids.add(t.target_db_id)
    data_sources = {ds.id: ds.name for ds in DataSource.query.filter(DataSource.id.in_(ds_ids)).all()}

    # 获取每个任务的最后执行状态
    result = []
    for t in tasks:
        task_dict = t.to_dict()
        task_dict['source_db_name'] = data_sources.get(t.source_db_id, 'Unknown')
        task_dict['target_db_name'] = data_sources.get(t.target_db_id, 'Unknown')

        # 获取最后执行状态
        last_execution = TaskExecution.query.filter_by(task_id=t.id).order_by(TaskExecution.start_time.desc()).first()
        if last_execution:
            task_dict['last_status'] = last_execution.status
            task_dict['last_execution_time'] = last_execution.start_time.isoformat() if last_execution.start_time else None
        else:
            task_dict['last_status'] = None
            task_dict['last_execution_time'] = None

        result.append(task_dict)

    return jsonify(result), 200


@elt_tasks_bp.route('/<int:task_id>', methods=['GET'])
@jwt_required()
def get_elt_task(task_id):
    user_id = int(get_jwt_identity())
    task = ELTTask.query.filter_by(id=task_id, created_by=user_id).first()
    if not task:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(task.to_dict()), 200


@elt_tasks_bp.route('', methods=['POST'])
@jwt_required()
def create_elt_task():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data or not data.get('name') or not data.get('source_db_id') or not data.get('target_db_id'):
        return jsonify({'error': 'Missing required fields'}), 400

    task = ELTTask(
        name=data['name'],
        description=data.get('description', ''),
        source_type=data.get('source_type', 'table'),
        source_db_id=data['source_db_id'],
        target_db_id=data['target_db_id'],
        source_table=data.get('source_table'),
        source_sql=data.get('source_sql'),
        target_table=data.get('target_table', ''),
        write_strategy=data.get('write_strategy', 'append'),
        created_by=user_id
    )

    if data.get('transformation_rules'):
        task.set_transformation_rules(data['transformation_rules'])
    if data.get('join_conditions'):
        task.set_join_conditions(data['join_conditions'])
    if data.get('time_filter'):
        task.set_time_filter(data['time_filter'])

    db.session.add(task)
    db.session.commit()
    return jsonify({'message': 'Created', 'task': task.to_dict()}), 201


@elt_tasks_bp.route('/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_elt_task(task_id):
    user_id = int(get_jwt_identity())
    task = ELTTask.query.filter_by(id=task_id, created_by=user_id).first()
    if not task:
        return jsonify({'error': 'Not found'}), 404

    data = request.get_json()

    # 更新基本字段
    for field in ['name', 'description', 'source_type', 'source_db_id', 'target_db_id', 'source_table', 'source_sql', 'target_table', 'write_strategy']:
        if data.get(field) is not None:
            setattr(task, field, data[field])

    # 更新JSON字段
    if 'transformation_rules' in data:
        task.set_transformation_rules(data['transformation_rules'])
    if 'join_conditions' in data:
        task.set_join_conditions(data['join_conditions'])
    if 'time_filter' in data:
        task.set_time_filter(data['time_filter'])

    db.session.commit()
    return jsonify({'message': 'Updated', 'task': task.to_dict()}), 200


@elt_tasks_bp.route('/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_elt_task(task_id):
    user_id = int(get_jwt_identity())
    task = ELTTask.query.filter_by(id=task_id, created_by=user_id).first()
    if not task:
        return jsonify({'error': 'Not found'}), 404

    db.session.delete(task)
    db.session.commit()
    return jsonify({'message': 'Deleted'}), 200


@elt_tasks_bp.route('/<int:task_id>/execute', methods=['POST'])
@jwt_required()
def execute_elt_task(task_id):
    """执行ELT任务"""
    user_id = int(get_jwt_identity())
    task = ELTTask.query.filter_by(id=task_id, created_by=user_id).first()
    if not task:
        return jsonify({'error': 'Not found'}), 404

    # 获取源和目标数据源
    source_ds = DataSource.query.get(task.source_db_id)
    target_ds = DataSource.query.get(task.target_db_id)

    if not source_ds:
        return jsonify({'error': '源数据源不存在'}), 400
    if not target_ds:
        return jsonify({'error': '目标数据源不存在'}), 400

    # 创建执行记录
    execution = TaskExecution(
        task_id=task_id,
        status='running',
        start_time=datetime.utcnow(),
        execution_log=f"开始执行任务: {task.name}"
    )
    db.session.add(execution)
    db.session.commit()

    try:
        # 执行ELT任务
        logger.info(f"Executing ELT task {task_id}: {task.name}")
        result = elt_engine.execute(task, source_ds, target_ds)

        # 更新执行记录
        execution.status = 'success'
        execution.end_time = datetime.utcnow()
        execution.processed_rows = result.get('processed_rows', 0)
        execution.execution_log = result.get('log', '')
        db.session.commit()

        logger.info(f"ELT task {task_id} completed successfully")

        return jsonify({
            'message': '执行成功',
            'execution_id': execution.id,
            'details': {
                'processed_rows': execution.processed_rows,
                'status': 'success',
                'log': execution.execution_log
            }
        }), 200

    except Exception as e:
        logger.error(f"ELT task {task_id} failed: {str(e)}")

        # 更新执行记录为失败
        execution.status = 'failed'
        execution.end_time = datetime.utcnow()
        execution.error_message = str(e)
        execution.execution_log = f"执行失败: {str(e)}"
        db.session.commit()

        return jsonify({
            'error': f'执行失败: {str(e)}',
            'execution_id': execution.id
        }), 500


@elt_tasks_bp.route('/<int:task_id>/preview', methods=['POST'])
@jwt_required()
def preview_elt_task(task_id):
    """预览ELT任务数据"""
    user_id = int(get_jwt_identity())
    task = ELTTask.query.filter_by(id=task_id, created_by=user_id).first()
    if not task:
        return jsonify({'error': 'Not found'}), 404

    source_ds = DataSource.query.get(task.source_db_id)
    if not source_ds:
        return jsonify({'error': '源数据源不存在'}), 400

    data = request.get_json()
    sql = data.get('sql') if data else None

    try:
        result = elt_engine.preview_sql(task, source_ds, sql)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500