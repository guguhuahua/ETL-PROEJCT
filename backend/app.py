"""
ELT System - Flask Application Entry Point
"""
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import os

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

    with app.app_context():
        db.create_all()

    return app


app = create_app(os.getenv('FLASK_ENV', 'development'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)