"""
Database Models
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import json

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {'id': self.id, 'username': self.username, 'email': self.email,
                'created_at': self.created_at.isoformat() if self.created_at else None}


class DataSource(db.Model):
    __tablename__ = 'data_sources'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    connection_params = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_connection_params(self):
        return json.loads(self.connection_params) if self.connection_params else {}

    def set_connection_params(self, params):
        self.connection_params = json.dumps(params)

    def to_dict(self, include_params=False):
        result = {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_params:
            params = self.get_connection_params()
            # 隐藏密码
            if 'password' in params:
                params = {**params, 'password': '******'}
            result['connection_params'] = params
        else:
            # 列表模式下返回简化的连接信息（不含密码）
            params = self.get_connection_params()
            result['connection_params'] = {
                'host': params.get('host', ''),
                'port': params.get('port', ''),
                'database': params.get('database', ''),
                'username': params.get('username', '')
            }
        return result


class ELTTask(db.Model):
    __tablename__ = 'elt_tasks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    source_type = db.Column(db.String(20), default='table')
    source_db_id = db.Column(db.Integer, nullable=False)
    target_db_id = db.Column(db.Integer, nullable=False)
    source_table = db.Column(db.String(100))
    source_sql = db.Column(db.Text)
    target_table = db.Column(db.String(100), nullable=False)
    write_strategy = db.Column(db.String(20), default='append')  # append: 追加, overwrite: 覆盖
    transformation_rules = db.Column(db.Text)
    join_conditions = db.Column(db.Text)
    time_filter = db.Column(db.Text)
    created_by = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_transformation_rules(self):
        return json.loads(self.transformation_rules) if self.transformation_rules else []

    def set_transformation_rules(self, rules):
        self.transformation_rules = json.dumps(rules)

    def get_join_conditions(self):
        return json.loads(self.join_conditions) if self.join_conditions else {}

    def set_join_conditions(self, conditions):
        self.join_conditions = json.dumps(conditions)

    def get_time_filter(self):
        return json.loads(self.time_filter) if self.time_filter else {}

    def set_time_filter(self, filter_config):
        self.time_filter = json.dumps(filter_config)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'source_type': self.source_type,
            'source_db_id': self.source_db_id,
            'target_db_id': self.target_db_id,
            'source_table': self.source_table,
            'source_sql': self.source_sql,
            'target_table': self.target_table,
            'write_strategy': self.write_strategy or 'append',
            'transformation_rules': self.get_transformation_rules(),
            'join_conditions': self.get_join_conditions(),
            'time_filter': self.get_time_filter(),
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Schedule(db.Model):
    __tablename__ = 'schedules'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    schedule_type = db.Column(db.String(20), nullable=False)
    schedule_config = db.Column(db.Text, nullable=False)
    dependencies = db.Column(db.Text)
    retry_count = db.Column(db.Integer, default=0)
    retry_interval = db.Column(db.Integer, default=300)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_schedule_config(self):
        return json.loads(self.schedule_config) if self.schedule_config else {}

    def set_schedule_config(self, config):
        self.schedule_config = json.dumps(config)

    def get_dependencies(self):
        return json.loads(self.dependencies) if self.dependencies else []

    def set_dependencies(self, deps):
        self.dependencies = json.dumps(deps)

    def to_dict(self):
        return {
            'id': self.id, 'task_id': self.task_id, 'name': self.name,
            'schedule_type': self.schedule_type, 'schedule_config': self.get_schedule_config(),
            'dependencies': self.get_dependencies(), 'retry_count': self.retry_count,
            'retry_interval': self.retry_interval, 'is_active': self.is_active, 'created_by': self.created_by
        }


class TaskExecution(db.Model):
    __tablename__ = 'task_executions'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, nullable=False)
    schedule_id = db.Column(db.Integer)
    status = db.Column(db.String(20), nullable=False, default='running')
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    processed_rows = db.Column(db.Integer, default=0)
    execution_log = db.Column(db.Text)
    error_message = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id, 'task_id': self.task_id, 'schedule_id': self.schedule_id,
            'status': self.status, 'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'processed_rows': self.processed_rows, 'error_message': self.error_message
        }


class Workflow(db.Model):
    __tablename__ = 'workflows'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    trigger_type = db.Column(db.String(20), nullable=False, default='manual')  # 'manual', 'cron', 'event'
    trigger_config = db.Column(db.Text)  # JSON: cron表达式等
    nodes = db.Column(db.Text, nullable=False)  # JSON: 节点定义数组
    edges = db.Column(db.Text, nullable=False)  # JSON: 边定义数组
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_trigger_config(self):
        return json.loads(self.trigger_config) if self.trigger_config else {}

    def set_trigger_config(self, config):
        self.trigger_config = json.dumps(config)

    def get_nodes(self):
        return json.loads(self.nodes) if self.nodes else []

    def set_nodes(self, nodes):
        self.nodes = json.dumps(nodes)

    def get_edges(self):
        return json.loads(self.edges) if self.edges else []

    def set_edges(self, edges):
        self.edges = json.dumps(edges)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'trigger_type': self.trigger_type,
            'trigger_config': self.get_trigger_config(),
            'nodes': self.get_nodes(),
            'edges': self.get_edges(),
            'is_active': self.is_active,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class WorkflowExecution(db.Model):
    __tablename__ = 'workflow_executions'
    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='running')  # 'running', 'success', 'failed', 'partial'
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    node_executions = db.Column(db.Text)  # JSON: 每个节点的执行状态
    error_message = db.Column(db.Text)

    def get_node_executions(self):
        return json.loads(self.node_executions) if self.node_executions else {}

    def set_node_executions(self, executions):
        self.node_executions = json.dumps(executions)

    def to_dict(self):
        return {
            'id': self.id,
            'workflow_id': self.workflow_id,
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'node_executions': self.get_node_executions(),
            'error_message': self.error_message
        }