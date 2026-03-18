"""
Workflow Engine Service
Handles workflow execution with task orchestration
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """Workflow execution engine for orchestrating multiple tasks"""

    def __init__(self):
        self.task_results = {}

    def execute(self, workflow) -> Dict[str, Any]:
        """
        Execute a workflow

        Args:
            workflow: Workflow model instance

        Returns:
            Dict with execution results
        """
        from models import db, ELTTask, DataSource, TaskExecution
        from services.elt_engine import elt_engine

        result = {
            'status': 'success',
            'node_executions': {},
            'processed_nodes': 0,
            'failed_nodes': 0,
            'start_time': datetime.utcnow().isoformat(),
            'end_time': None,
            'error_message': None
        }

        nodes = workflow.get_nodes()
        edges = workflow.get_edges()

        if not nodes:
            result['status'] = 'success'
            result['end_time'] = datetime.utcnow().isoformat()
            return result

        try:
            # Build adjacency list
            graph = self._build_graph(nodes, edges)

            # Find start node
            start_node = self._find_start_node(nodes)
            if not start_node:
                raise ValueError("未找到开始节点")

            # Topological sort to determine execution order
            execution_order = self._topological_sort(nodes, edges)
            logger.info(f"Execution order: {[n['id'] for n in execution_order]}")

            # Track task execution records
            task_executions = {}

            # Execute nodes in order
            for node in execution_order:
                node_id = node.get('id')
                node_type = node.get('type')

                logger.info(f"Executing node: {node_id} (type: {node_type})")

                node_result = {
                    'node_id': node_id,
                    'node_type': node_type,
                    'label': node.get('label', ''),
                    'status': 'pending',
                    'start_time': datetime.utcnow().isoformat(),
                    'end_time': None,
                    'error': None
                }

                try:
                    if node_type == 'START':
                        # Start node - just mark as success
                        node_result['status'] = 'success'
                        node_result['message'] = '开始节点'

                    elif node_type == 'END':
                        # End node - mark as success
                        node_result['status'] = 'success'
                        node_result['message'] = '结束节点'

                    elif node_type == 'TASK':
                        # Task node - execute the associated task
                        task_id = node.get('taskId')
                        if not task_id:
                            raise ValueError(f"任务节点 {node_id} 未关联任务")

                        task = ELTTask.query.get(task_id)
                        if not task:
                            raise ValueError(f"任务ID {task_id} 不存在")

                        # Get data sources
                        source_ds = DataSource.query.get(task.source_db_id)
                        target_ds = DataSource.query.get(task.target_db_id)

                        if not source_ds:
                            raise ValueError(f"源数据源ID {task.source_db_id} 不存在")
                        if not target_ds:
                            raise ValueError(f"目标数据源ID {task.target_db_id} 不存在")

                        # Create task execution record
                        execution = TaskExecution(
                            task_id=task_id,
                            status='running',
                            start_time=datetime.utcnow(),
                            execution_log=f"通过工作流 '{workflow.name}' 触发执行"
                        )
                        db.session.add(execution)
                        db.session.commit()

                        try:
                            # Execute the task
                            task_result = elt_engine.execute(task, source_ds, target_ds)

                            # Update execution record
                            execution.status = 'success'
                            execution.end_time = datetime.utcnow()
                            execution.processed_rows = task_result.get('processed_rows', 0)
                            execution.execution_log = task_result.get('log', '')
                            db.session.commit()

                            node_result['status'] = 'success'
                            node_result['task_id'] = task_id
                            node_result['task_name'] = task.name
                            node_result['processed_rows'] = task_result.get('processed_rows', 0)
                            node_result['execution_id'] = execution.id

                            # Store for parallel branches
                            self.task_results[node_id] = {
                                'success': True,
                                'processed_rows': task_result.get('processed_rows', 0)
                            }

                        except Exception as task_error:
                            # Update execution record as failed
                            execution.status = 'failed'
                            execution.end_time = datetime.utcnow()
                            execution.error_message = str(task_error)
                            db.session.commit()

                            raise task_error

                    elif node_type == 'CONDITION':
                        # Condition node - evaluate and determine next path
                        condition_config = node.get('condition', {})
                        condition_type = condition_config.get('type', 'success')

                        # Check upstream task result
                        upstream_nodes = self._get_upstream_nodes(node_id, edges)
                        condition_met = True

                        for up_id in upstream_nodes:
                            up_result = result['node_executions'].get(up_id, {})
                            if condition_type == 'success':
                                condition_met = up_result.get('status') == 'success'
                            elif condition_type == 'failure':
                                condition_met = up_result.get('status') == 'failed'

                        node_result['status'] = 'success'
                        node_result['condition_met'] = condition_met
                        node_result['message'] = f"条件判断: {condition_type}"

                    elif node_type == 'PARALLEL':
                        # Parallel node - execute branches in parallel
                        branches = node.get('branches', [])
                        if branches:
                            node_result['branches'] = []
                            node_result['status'] = 'success'

                            # Parallel execution would be handled by the graph structure
                            # Here we just mark the parallel node as executed
                            node_result['message'] = f"并行分支节点: {len(branches)} 个分支"
                        else:
                            node_result['status'] = 'success'
                            node_result['message'] = '并行分支节点'

                    result['processed_nodes'] += 1

                except Exception as e:
                    logger.error(f"Node {node_id} execution failed: {str(e)}")
                    node_result['status'] = 'failed'
                    node_result['error'] = str(e)
                    result['failed_nodes'] += 1

                    # Check if we should continue or stop
                    if node_type == 'TASK':
                        # For task nodes, we can continue with other branches
                        result['status'] = 'partial'
                    else:
                        # For other nodes, stop execution
                        result['status'] = 'failed'
                        result['error_message'] = f"节点 {node_id} 执行失败: {str(e)}"
                        break

                node_result['end_time'] = datetime.utcnow().isoformat()
                result['node_executions'][node_id] = node_result

            # Determine final status
            if result['failed_nodes'] > 0:
                if result['processed_nodes'] > result['failed_nodes']:
                    result['status'] = 'partial'
                else:
                    result['status'] = 'failed'

            result['end_time'] = datetime.utcnow().isoformat()
            return result

        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            result['status'] = 'failed'
            result['error_message'] = str(e)
            result['end_time'] = datetime.utcnow().isoformat()
            return result

    def _build_graph(self, nodes: List[Dict], edges: List[Dict]) -> Dict[str, List[str]]:
        """Build adjacency list from nodes and edges"""
        graph = {n.get('id'): [] for n in nodes}
        for edge in edges:
            source = edge.get('source')
            target = edge.get('target')
            if source in graph:
                graph[source].append(target)
        return graph

    def _find_start_node(self, nodes: List[Dict]) -> Optional[Dict]:
        """Find the start node"""
        for node in nodes:
            if node.get('type') == 'START':
                return node
        return None

    def _get_upstream_nodes(self, node_id: str, edges: List[Dict]) -> List[str]:
        """Get upstream nodes for a given node"""
        upstream = []
        for edge in edges:
            if edge.get('target') == node_id:
                upstream.append(edge.get('source'))
        return upstream

    def _topological_sort(self, nodes: List[Dict], edges: List[Dict]) -> List[Dict]:
        """
        Perform topological sort on the workflow graph
        Returns nodes in execution order
        """
        # Build adjacency list and in-degree count
        node_map = {n.get('id'): n for n in nodes}
        graph = {n.get('id'): [] for n in nodes}
        in_degree = {n.get('id'): 0 for n in nodes}

        for edge in edges:
            source = edge.get('source')
            target = edge.get('target')
            if source in graph and target in in_degree:
                graph[source].append(target)
                in_degree[target] += 1

        # Kahn's algorithm for topological sort
        queue = deque()
        for node_id, degree in in_degree.items():
            if degree == 0:
                queue.append(node_id)

        result = []
        while queue:
            node_id = queue.popleft()
            result.append(node_map[node_id])

            for neighbor in graph[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return result

    def validate_workflow(self, nodes: List[Dict], edges: List[Dict]) -> Dict[str, Any]:
        """Validate workflow configuration"""
        errors = []

        # Check for start node
        start_nodes = [n for n in nodes if n.get('type') == 'START']
        if len(start_nodes) == 0:
            errors.append('必须包含一个开始节点')
        elif len(start_nodes) > 1:
            errors.append('只能有一个开始节点')

        # Check for end node
        end_nodes = [n for n in nodes if n.get('type') == 'END']
        if len(end_nodes) == 0:
            errors.append('必须包含至少一个结束节点')

        # Check for cycles
        if self._has_cycle(nodes, edges):
            errors.append('工作流存在循环依赖')

        # Check task nodes have taskId
        for node in nodes:
            if node.get('type') == 'TASK':
                if not node.get('taskId'):
                    errors.append(f'任务节点 "{node.get("label", node.get("id"))}" 未关联任务')

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

    def _has_cycle(self, nodes: List[Dict], edges: List[Dict]) -> bool:
        """Check if the workflow graph has a cycle"""
        graph = self._build_graph(nodes, edges)

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


# Singleton instance
workflow_engine = WorkflowEngine()