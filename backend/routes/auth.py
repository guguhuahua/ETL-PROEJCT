"""
Authentication Routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from models import db, User
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import base64
import os

auth_bp = Blueprint('auth', __name__)

# RSA密钥对（生产环境应从环境变量或文件加载）
PRIVATE_KEY = None
PUBLIC_KEY = None
PUBLIC_KEY_PEM = None


def init_rsa_keys():
    """初始化RSA密钥对"""
    global PRIVATE_KEY, PUBLIC_KEY, PUBLIC_KEY_PEM

    # 尝试从环境变量加载私钥
    private_key_pem = os.environ.get('RSA_PRIVATE_KEY')

    if private_key_pem:
        PRIVATE_KEY = serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=None,
            backend=default_backend()
        )
    else:
        # 生成新的密钥对
        PRIVATE_KEY = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

    PUBLIC_KEY = PRIVATE_KEY.public_key()

    # 导出公钥PEM格式（去除头尾和换行，方便前端使用）
    public_key_pem = PUBLIC_KEY.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    PUBLIC_KEY_PEM = public_key_pem.decode().replace('-----BEGIN PUBLIC KEY-----', '').replace('-----END PUBLIC KEY-----', '').replace('\n', '')


def decrypt_password(encrypted_b64):
    """解密前端传输的密码"""
    try:
        encrypted_data = base64.b64decode(encrypted_b64)
        decrypted = PRIVATE_KEY.decrypt(
            encrypted_data,
            padding.PKCS1v15()
        )
        return decrypted.decode('utf-8')
    except Exception as e:
        print(f"[登录] 密码解密失败: {e}")
        return None


@auth_bp.route('/public-key', methods=['GET'])
def get_public_key():
    """获取RSA公钥"""
    return jsonify({'public_key': PUBLIC_KEY_PEM}), 200


@auth_bp.route('/register', methods=['POST'])
def register():
    """注册功能已关闭"""
    return jsonify({'error': '注册功能已关闭，请联系管理员'}), 403


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Missing username or password'}), 400

    username = data['username'].strip()

    # 解密密码
    encrypted_password = data['password']
    password = decrypt_password(encrypted_password)

    if password is None:
        # 兼容旧版本：如果解密失败，尝试直接使用（开发环境）
        password = encrypted_password

    user = User.query.filter((User.username == username) | (User.email == username)).first()

    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid username or password'}), 401

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    return jsonify({'message': 'Logout successful'}), 200


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user.to_dict()), 200