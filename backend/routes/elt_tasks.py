"""
ELT Task Routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone
from models import db, ELTTask, TaskExecution, DataSource
from services.elt_engine import elt_engine
import logging

logger = logging.getLogger(__name__)
elt_tasks_bp = Blueprint('elt_tasks', __name__)


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
            dt = dt.replace(tzinfo=timezone.utc)

        # 转换为本地时区
        local_dt = dt.astimezone(LOCAL_TZ)

        # 返回标准格式字符串
        return local_dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        logger.error(f"Error formatting datetime: {e}")
        return str(dt) if dt else None


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
        task_dict['created_at'] = format_datetime_local(t.created_at)

        # 获取最后执行状态
        last_execution = TaskExecution.query.filter_by(task_id=t.id).order_by(TaskExecution.start_time.desc()).first()
        if last_execution:
            task_dict['last_status'] = last_execution.status
            task_dict['last_execution_time'] = format_datetime_local(last_execution.start_time)
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

    # 检查是否有正在运行的任务
    running_execution = TaskExecution.query.filter_by(
        task_id=task_id,
        status='running'
    ).first()
    if running_execution:
        return jsonify({
            'error': '该任务正在执行中，请等待完成或取消当前执行',
            'execution_id': running_execution.id
        }), 400

    # 获取源和目标数据源
    source_ds = DataSource.query.get(task.source_db_id)
    target_ds = DataSource.query.get(task.target_db_id)

    if not source_ds:
        return jsonify({'error': '源数据源不存在'}), 400
    if not target_ds:
        return jsonify({'error': '目标数据源不存在'}), 400

    print(f"\n{'='*60}")
    print(f"[执行任务] 开始执行ELT任务: {task.name}")
    print(f"[执行任务] 任务ID: {task_id}")
    print(f"[执行任务] 写入策略: {task.write_strategy}")
    print(f"[执行任务] 源: {source_ds.name}, 目标: {target_ds.name}")
    print(f"{'='*60}\n")

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

        print(f"\n[执行任务] 任务执行成功! 处理 {execution.processed_rows} 行\n")

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
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()

        print(f"\n[执行任务] 任务执行失败: {error_msg}")
        print(f"[执行任务] 错误堆栈:\n{error_trace}\n")

        logger.error(f"ELT task {task_id} failed: {error_msg}")
        logger.error(error_trace)

        # 更新执行记录为失败
        try:
            execution.status = 'failed'
            execution.end_time = datetime.utcnow()
            execution.error_message = error_msg
            execution.execution_log = f"执行失败: {error_msg}\n\n{error_trace}"
            db.session.commit()
        except Exception as db_error:
            logger.error(f"Failed to update execution status: {db_error}")
            db.session.rollback()

        return jsonify({
            'error': f'执行失败: {error_msg}',
            'execution_id': execution.id
        }), 500


@elt_tasks_bp.route('/executions/<int:execution_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_execution(execution_id):
    """取消正在执行的任务"""
    user_id = int(get_jwt_identity())
    execution = TaskExecution.query.get(execution_id)
    if not execution:
        return jsonify({'error': '执行记录不存在'}), 404

    # 验证任务归属
    task = ELTTask.query.get(execution.task_id)
    if not task or task.created_by != user_id:
        return jsonify({'error': '无权限操作'}), 403

    if execution.status != 'running':
        return jsonify({'error': '该任务不在运行状态'}), 400

    # 标记为已取消
    execution.status = 'cancelled'
    execution.end_time = datetime.utcnow()
    execution.error_message = '用户手动取消'
    db.session.commit()

    print(f"[执行任务] 任务 {execution.task_id} 的执行 {execution_id} 已被取消")

    return jsonify({
        'message': '已取消',
        'execution_id': execution.id
    }), 200


@elt_tasks_bp.route('/<int:task_id>/running', methods=['GET'])
@jwt_required()
def get_running_execution(task_id):
    """获取任务正在运行的执行记录"""
    user_id = int(get_jwt_identity())
    task = ELTTask.query.filter_by(id=task_id, created_by=user_id).first()
    if not task:
        return jsonify({'error': 'Not found'}), 404

    running_execution = TaskExecution.query.filter_by(
        task_id=task_id,
        status='running'
    ).first()

    if running_execution:
        return jsonify({
            'running': True,
            'execution': {
                'id': running_execution.id,
                'start_time': format_datetime_local(running_execution.start_time),
                'status': running_execution.status
            }
        }), 200
    else:
        return jsonify({'running': False, 'execution': None}), 200


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