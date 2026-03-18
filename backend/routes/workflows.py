"""
Workflow Routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from models import db, Workflow, WorkflowExecution, ELTTask, DataSource
from services.workflow_engine import workflow_engine
import logging

logger = logging.getLogger(__name__)
workflows_bp = Blueprint('workflows', __name__)


@workflows_bp.route('', methods=['GET'])
@jwt_required()
def get_workflows():
    """获取所有工作流"""
    user_id = int(get_jwt_identity())
    workflows = Workflow.query.filter_by(created_by=user_id).order_by(Workflow.created_at.desc()).all()

    result = []
    for wf in workflows:
        wf_dict = wf.to_dict()
        # 获取最后执行状态
        last_execution = WorkflowExecution.query.filter_by(workflow_id=wf.id).order_by(
            WorkflowExecution.start_time.desc()
        ).first()
        if last_execution:
            wf_dict['last_status'] = last_execution.status
            wf_dict['last_execution_time'] = last_execution.start_time.isoformat() if last_execution.start_time else None
        else:
            wf_dict['last_status'] = None
            wf_dict['last_execution_time'] = None
        result.append(wf_dict)

    return jsonify(result), 200


@workflows_bp.route('/<int:wf_id>', methods=['GET'])
@jwt_required()
def get_workflow(wf_id):
    """获取单个工作流详情"""
    user_id = int(get_jwt_identity())
    wf = Workflow.query.filter_by(id=wf_id, created_by=user_id).first()
    if not wf:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(wf.to_dict()), 200


@workflows_bp.route('', methods=['POST'])
@jwt_required()
def create_workflow():
    """创建工作流"""
    user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data or not data.get('name'):
        return jsonify({'error': 'Missing required fields: name'}), 400

    nodes = data.get('nodes', [])
    edges = data.get('edges', [])

    # 验证节点
    validation_result = validate_workflow(nodes, edges)
    if not validation_result['valid']:
        return jsonify({'error': validation_result['message']}), 400

    wf = Workflow(
        name=data['name'],
        description=data.get('description', ''),
        trigger_type=data.get('trigger_type', 'manual'),
        created_by=user_id
    )

    if data.get('trigger_config'):
        wf.set_trigger_config(data['trigger_config'])
    wf.set_nodes(nodes)
    wf.set_edges(edges)

    db.session.add(wf)
    db.session.commit()

    return jsonify({'message': 'Created', 'workflow': wf.to_dict()}), 201


@workflows_bp.route('/<int:wf_id>', methods=['PUT'])
@jwt_required()
def update_workflow(wf_id):
    """更新工作流"""
    user_id = int(get_jwt_identity())
    wf = Workflow.query.filter_by(id=wf_id, created_by=user_id).first()
    if not wf:
        return jsonify({'error': 'Not found'}), 404

    data = request.get_json()

    # 更新基本字段
    if data.get('name'):
        wf.name = data['name']
    if data.get('description') is not None:
        wf.description = data['description']
    if data.get('trigger_type'):
        wf.trigger_type = data['trigger_type']
    if data.get('is_active') is not None:
        wf.is_active = data['is_active']

    # 更新JSON字段
    if 'trigger_config' in data:
        wf.set_trigger_config(data['trigger_config'])

    nodes = data.get('nodes')
    edges = data.get('edges')

    if nodes is not None or edges is not None:
        nodes = nodes if nodes is not None else wf.get_nodes()
        edges = edges if edges is not None else wf.get_edges()

        # 验证节点
        validation_result = validate_workflow(nodes, edges)
        if not validation_result['valid']:
            return jsonify({'error': validation_result['message']}), 400

        if nodes is not None:
            wf.set_nodes(nodes)
        if edges is not None:
            wf.set_edges(edges)

    db.session.commit()
    return jsonify({'message': 'Updated', 'workflow': wf.to_dict()}), 200


@workflows_bp.route('/<int:wf_id>', methods=['DELETE'])
@jwt_required()
def delete_workflow(wf_id):
    """删除工作流"""
    user_id = int(get_jwt_identity())
    wf = Workflow.query.filter_by(id=wf_id, created_by=user_id).first()
    if not wf:
        return jsonify({'error': 'Not found'}), 404

    # 删除相关执行记录
    WorkflowExecution.query.filter_by(workflow_id=wf_id).delete()

    db.session.delete(wf)
    db.session.commit()
    return jsonify({'message': 'Deleted'}), 200


@workflows_bp.route('/<int:wf_id>/execute', methods=['POST'])
@jwt_required()
def execute_workflow(wf_id):
    """执行工作流"""
    user_id = int(get_jwt_identity())
    wf = Workflow.query.filter_by(id=wf_id, created_by=user_id).first()
    if not wf:
        return jsonify({'error': 'Not found'}), 404

    if not wf.is_active:
        return jsonify({'error': '工作流未激活'}), 400

    # 创建执行记录
    execution = WorkflowExecution(
        workflow_id=wf_id,
        status='running',
        start_time=datetime.utcnow()
    )
    db.session.add(execution)
    db.session.commit()

    try:
        logger.info(f"Executing workflow {wf_id}: {wf.name}")
        result = workflow_engine.execute(wf)

        # 更新执行记录
        execution.status = result.get('status', 'success')
        execution.end_time = datetime.utcnow()
        execution.set_node_executions(result.get('node_executions', {}))
        if result.get('error_message'):
            execution.error_message = result['error_message']
        db.session.commit()

        logger.info(f"Workflow {wf_id} completed with status: {execution.status}")

        return jsonify({
            'message': '工作流执行完成',
            'execution_id': execution.id,
            'status': execution.status,
            'details': result
        }), 200

    except Exception as e:
        logger.error(f"Workflow {wf_id} failed: {str(e)}")

        execution.status = 'failed'
        execution.end_time = datetime.utcnow()
        execution.error_message = str(e)
        db.session.commit()

        return jsonify({
            'error': f'工作流执行失败: {str(e)}',
            'execution_id': execution.id
        }), 500


@workflows_bp.route('/<int:wf_id>/executions', methods=['GET'])
@jwt_required()
def get_workflow_executions(wf_id):
    """获取工作流执行历史"""
    user_id = int(get_jwt_identity())
    wf = Workflow.query.filter_by(id=wf_id, created_by=user_id).first()
    if not wf:
        return jsonify({'error': 'Not found'}), 404

    executions = WorkflowExecution.query.filter_by(workflow_id=wf_id).order_by(
        WorkflowExecution.start_time.desc()
    ).limit(50).all()

    return jsonify([e.to_dict() for e in executions]), 200


@workflows_bp.route('/<int:wf_id>/toggle', methods=['POST'])
@jwt_required()
def toggle_workflow(wf_id):
    """启用/禁用工作流"""
    user_id = int(get_jwt_identity())
    wf = Workflow.query.filter_by(id=wf_id, created_by=user_id).first()
    if not wf:
        return jsonify({'error': 'Not found'}), 404

    wf.is_active = not wf.is_active
    db.session.commit()

    return jsonify({
        'message': '状态已更新',
        'is_active': wf.is_active
    }), 200


def validate_workflow(nodes, edges):
    """验证工作流配置"""
    if not nodes:
        return {'valid': True, 'message': ''}

    node_ids = {n.get('id') for n in nodes}

    # 检查开始节点
    start_nodes = [n for n in nodes if n.get('type') == 'START']
    if len(start_nodes) == 0:
        return {'valid': False, 'message': '必须包含一个开始节点'}
    if len(start_nodes) > 1:
        return {'valid': False, 'message': '只能有一个开始节点'}

    # 检查边是否引用有效的节点
    for edge in edges:
        source = edge.get('source')
        target = edge.get('target')
        if source not in node_ids:
            return {'valid': False, 'message': f'边的源节点 {source} 不存在'}
        if target not in node_ids:
            return {'valid': False, 'message': f'边的目标节点 {target} 不存在'}

    # 检查循环依赖
    if has_cycle(nodes, edges):
        return {'valid': False, 'message': '工作流存在循环依赖'}

    # 验证节点类型
    allowed_node_types = {'START', 'TASK', 'CONDITION', 'PARALLEL', 'END'}
    for node in nodes:
        node_type = node.get('type')
        if node_type not in allowed_node_types:
            return {'valid': False, 'message': f'节点类型不合法：{node_type}'}

    # 校验边不重复以及在节点范围内
    seen_edges = set()
    for edge in edges:
        source = edge.get('source')
        target = edge.get('target')
        if source not in node_ids:
            return {'valid': False, 'message': f'边的源节点 {source} 不存在'}
        if target not in node_ids:
            return {'valid': False, 'message': f'边的目标节点 {target} 不存在'}

        edge_key = (source, target)
        if edge_key in seen_edges:
            return {'valid': False, 'message': f'重复的连线: {source} -> {target}'}
        seen_edges.add(edge_key)

    # 检查任务节点是否关联了有效的任务
    for node in nodes:
        if node.get('type') == 'TASK':
            task_id = node.get('taskId')
            if not task_id:
                return {'valid': False, 'message': f'任务节点 {node.get("id")} 必须关联 taskId'}
            task = ELTTask.query.get(task_id)
            if not task:
                return {'valid': False, 'message': f'任务节点关联的任务ID {task_id} 不存在'}

    return {'valid': True, 'message': ''}


def has_cycle(nodes, edges):
    """检测工作流是否存在循环"""
    if not edges:
        return False

    # 构建邻接表
    graph = {n.get('id'): [] for n in nodes}
    for edge in edges:
        source = edge.get('source')
        target = edge.get('target')
        if source in graph:
            graph[source].append(target)

    # DFS检测循环
    visited = set()
    rec_stack = set()

    def dfs(node):
        visited.add(node)
        rec_stack.add(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True

        rec_stack.remove(node)
        return False

    for node in graph:
        if node not in visited:
            if dfs(node):
                return True

    return False