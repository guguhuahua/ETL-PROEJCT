"""
初始化脚本 - 创建测试用户
运行方式: python init_db.py
"""
from app import app, db
from models import User

def init_database():
    with app.app_context():
        # 创建所有表
        db.create_all()

        # 检查是否已存在测试用户
        test_user = User.query.filter_by(username='test').first()
        if test_user:
            print("测试用户已存在!")
            print(f"用户名: test")
            print(f"邮箱: {test_user.email}")
            return

        # 创建测试用户
        test_user = User()
        test_user.username = 'test'
        test_user.email = 'test@example.com'
        test_user.set_password('test123')

        db.session.add(test_user)
        db.session.commit()

        print("=" * 40)
        print("测试用户创建成功!")
        print("=" * 40)
        print("用户名: test")
        print("密码: test123")
        print("邮箱: test@example.com")
        print("=" * 40)


if __name__ == '__main__':
    init_database()