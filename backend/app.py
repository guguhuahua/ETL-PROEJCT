"""
ELT System - Flask Application Entry Point
"""
from flask import Flask, send_from_directory
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import db and models from models package
from models import db, User, DataSource, ELTTask, Schedule, TaskExecution, Workflow, WorkflowExecution

jwt = JWTManager()


def create_app(config_name='default'):
    from config import config

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    jwt.init_app(app)
    CORS(app, resources={
        r'/api/*': {
            'origins': app.config.get('CORS_ORIGINS', ['*']),
            'methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
            'allow_headers': ['Content-Type', 'Authorization'],
            'supports_credentials': True
        }
    })

    # Register blueprints
    from routes.auth import auth_bp
    from routes.data_sources import data_sources_bp
    from routes.elt_tasks import elt_tasks_bp
    from routes.schedules import schedules_bp
    from routes.task_executions import task_executions_bp
    from routes.workflows import workflows_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(data_sources_bp, url_prefix='/api/data-sources')
    app.register_blueprint(elt_tasks_bp, url_prefix='/api/elt-tasks')
    app.register_blueprint(schedules_bp, url_prefix='/api/schedules')
    app.register_blueprint(task_executions_bp, url_prefix='/api/task-executions')
    app.register_blueprint(workflows_bp, url_prefix='/api/workflows')

    # 设置静态文件目录（Docker环境）
    static_folder = '/app/frontend/dist' if os.path.exists('/app/frontend/dist') else None
    if static_folder:
        app.static_folder = static_folder

        @app.route('/', defaults={'path': ''})
        @app.route('/<path:path>')
        def serve_frontend(path):
            # API请求交给蓝图处理
            if path.startswith('api/'):
                return {'error': 'Not found'}, 404
            # 静态文件
            if path and os.path.exists(os.path.join(app.static_folder, path)):
                return send_from_directory(app.static_folder, path)
            # SPA应用，返回index.html
            return send_from_directory(app.static_folder, 'index.html')

    with app.app_context():
        db.create_all()

    return app


app = create_app(os.getenv('FLASK_ENV', 'development'))

# 初始化调度器
with app.app_context():
    from services.scheduler import init_scheduler
    init_scheduler(app)

# 初始化RSA密钥
from routes.auth import init_rsa_keys
init_rsa_keys()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)