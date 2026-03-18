"""
Data Source Routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, DataSource
from services.db_connector import get_connector
import json

data_sources_bp = Blueprint('data_sources', __name__)


@data_sources_bp.route('', methods=['GET'])
@jwt_required()
def get_data_sources():
    user_id = int(get_jwt_identity())
    data_sources = DataSource.query.filter_by(created_by=user_id).all()
    return jsonify([ds.to_dict() for ds in data_sources]), 200


@data_sources_bp.route('/<int:ds_id>', methods=['GET'])
@jwt_required()
def get_data_source(ds_id):
    """获取单个数据源详情"""
    user_id = int(get_jwt_identity())
    ds = DataSource.query.filter_by(id=ds_id, created_by=user_id).first()
    if not ds:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(ds.to_dict(include_params=True)), 200


@data_sources_bp.route('', methods=['POST'])
@jwt_required()
def create_data_source():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    if not data or not data.get('name') or not data.get('type'):
        return jsonify({'error': 'Missing required fields'}), 400

    ds = DataSource(name=data['name'], type=data['type'], created_by=user_id)
    ds.set_connection_params(data.get('connection_params', {}))
    db.session.add(ds)
    db.session.commit()
    return jsonify({'message': 'Created', 'data_source': ds.to_dict()}), 201


@data_sources_bp.route('/<int:ds_id>', methods=['PUT'])
@jwt_required()
def update_data_source(ds_id):
    user_id = int(get_jwt_identity())
    ds = DataSource.query.filter_by(id=ds_id, created_by=user_id).first()
    if not ds:
        return jsonify({'error': 'Not found'}), 404

    data = request.get_json()
    if data.get('name'):
        ds.name = data['name']
    if data.get('type'):
        ds.type = data['type']
    if data.get('connection_params'):
        ds.set_connection_params(data['connection_params'])

    db.session.commit()
    return jsonify({'message': 'Updated', 'data_source': ds.to_dict()}), 200


@data_sources_bp.route('/<int:ds_id>', methods=['DELETE'])
@jwt_required()
def delete_data_source(ds_id):
    user_id = int(get_jwt_identity())
    ds = DataSource.query.filter_by(id=ds_id, created_by=user_id).first()
    if not ds:
        return jsonify({'error': 'Not found'}), 404

    db.session.delete(ds)
    db.session.commit()
    return jsonify({'message': 'Deleted'}), 200


@data_sources_bp.route('/test-connection', methods=['POST'])
@jwt_required()
def test_connection():
    """测试数据库连接"""
    data = request.get_json()
    if not data or not data.get('type') or not data.get('connection_params'):
        return jsonify({'error': 'Missing required fields'}), 400

    db_type = data['type']
    params = data['connection_params']

    try:
        connector = get_connector(db_type, params)
        result = connector.test_connection()
        if result.get('success'):
            return jsonify({'success': True, 'message': result.get('message', '连接成功')}), 200
        else:
            return jsonify({'success': False, 'message': result.get('error', '连接失败')}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@data_sources_bp.route('/<int:ds_id>/tables', methods=['GET'])
@jwt_required()
def get_tables(ds_id):
    """获取数据源的所有表列表"""
    user_id = int(get_jwt_identity())
    ds = DataSource.query.filter_by(id=ds_id, created_by=user_id).first()
    if not ds:
        return jsonify({'error': 'Not found'}), 404

    try:
        connector = get_connector(ds.type, ds.get_connection_params())
        tables = connector.get_tables()
        return jsonify({'tables': tables}), 200
    except Exception as e:
        return jsonify({'error': f'获取表列表失败: {str(e)}'}), 500


@data_sources_bp.route('/<int:ds_id>/tables/<path:table_name>/columns', methods=['GET'])
@jwt_required()
def get_columns(ds_id, table_name):
    """获取表的字段列表"""
    user_id = int(get_jwt_identity())
    ds = DataSource.query.filter_by(id=ds_id, created_by=user_id).first()
    if not ds:
        return jsonify({'error': 'Not found'}), 404

    try:
        connector = get_connector(ds.type, ds.get_connection_params())
        columns = connector.get_columns(table_name)
        return jsonify({'columns': columns, 'table': table_name}), 200
    except Exception as e:
        return jsonify({'error': f'获取字段列表失败: {str(e)}'}), 500


@data_sources_bp.route('/<int:ds_id>/test-sql', methods=['POST'])
@jwt_required()
def test_sql(ds_id):
    """测试SQL查询并返回字段列表"""
    user_id = int(get_jwt_identity())
    ds = DataSource.query.filter_by(id=ds_id, created_by=user_id).first()
    if not ds:
        return jsonify({'error': 'Not found'}), 404

    data = request.get_json()
    sql = data.get('sql', '').strip()

    if not sql:
        return jsonify({'error': 'SQL语句不能为空'}), 400

    # 验证是否为SELECT语句
    sql_upper = sql.upper().strip()
    if not sql_upper.startswith('SELECT'):
        return jsonify({'error': '仅支持SELECT查询语句'}), 400

    try:
        connector = get_connector(ds.type, ds.get_connection_params())

        # 检查SQL是否已有LIMIT
        sql_upper = sql.upper()
        if 'LIMIT' not in sql_upper:
            test_sql = f"{sql} LIMIT 1"
        else:
            test_sql = sql

        # 执行SQL获取字段信息
        results = connector.execute_query(test_sql)

        # 获取字段信息（从结果推断类型）
        columns = []
        if results:
            for key in results[0].keys():
                value = results[0][key]
                col_type = type(value).__name__ if value is not None else 'UNKNOWN'

                # 将Python类型映射到更友好的类型名称
                type_mapping = {
                    'int': 'INTEGER',
                    'float': 'FLOAT',
                    'str': 'STRING',
                    'bool': 'BOOLEAN',
                    'datetime': 'DATETIME',
                    'date': 'DATE',
                    'time': 'TIME',
                    'NoneType': 'UNKNOWN'
                }
                col_type = type_mapping.get(col_type, col_type.upper())

                columns.append({
                    'name': key,
                    'type': col_type
                })

        return jsonify({
            'success': True,
            'message': 'SQL测试成功',
            'columns': columns,
            'preview_count': len(results)
        }), 200
    except Exception as e:
        return jsonify({'error': f'SQL执行失败: {str(e)}'}), 500