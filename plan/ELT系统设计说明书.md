# ELT系统设计说明书

## 上下文
本设计旨在创建一个前后端分离的ELT（提取、加载、转换）系统，满足以下核心需求：
- 前端使用Vue+Element UI
- 后端使用Flask+SQLite
- 包含账号注册登录功能
- 支持数据源管理（初期支持Hive和Kingbase8）
- 实现ELT配置功能（跨数据库迁移、字段转换、时间范围选择、JOIN操作）
- 调度配置功能（定时任务、依赖关系、失败重试）

## 推荐方法
分阶段实施，从基础架构到高级功能逐步完善。

## 关键文件路径
- 前端: frontend/src/
- 后端: backend/app.py, backend/models/, backend/routes/
- 数据库: backend/database.db (SQLite)

## 验证方式
通过单元测试、集成测试和端到端测试验证各模块功能，最终进行整体系统测试。

---

## 系统架构设计说明书

### 1. 整体架构概述

本系统采用前后端分离架构模式，前端基于Vue.js框架配合Element UI组件库构建用户界面，后端使用Flask轻量级Web框架提供RESTful API接口，数据库采用SQLite作为本地存储解决方案。

#### 1.1 架构层次
- 前端展示层：Vue.js + Element UI
- 后端服务层：Flask Web框架
- 数据访问层：SQLAlchemy ORM
- 数据存储层：SQLite数据库

#### 1.2 技术栈
- 前端：Vue.js 3.x, Element Plus UI, Axios
- 后端：Python 3.x, Flask 2.x, SQLAlchemy, Flask-JWT-Extended
- 数据库：SQLite 3.x
- 构建工具：npm, webpack
- 任务调度：APScheduler

### 2. 模块划分

#### 2.1 用户认证模块
- 用户注册/登录
- JWT令牌管理
- 权限控制

#### 2.2 数据源管理模块
- 数据源配置存储
- 连接测试
- 多数据库类型支持（Hive、Kingbase8）

#### 2.3 ELT配置模块
- 数据迁移规则定义
- 字段类型转换映射
- JOIN操作配置
- 时间范围过滤

#### 2.4 调度管理模块
- 定时任务配置
- 任务依赖关系管理
- 失败重试机制

### 3. 通信协议

- 前后端通信：HTTP/HTTPS + RESTful API
- 认证方式：JWT Token
- 数据格式：JSON
- API规范：遵循RESTful风格

## 概要设计说明书

### 1. 功能模块设计

#### 1.1 用户认证模块
- 实现用户注册、登录、登出功能
- 使用JWT进行身份验证
- 实现权限控制中间件

#### 1.2 数据源管理模块
- 设计数据源配置的数据模型
- 支持多种数据库类型的连接参数配置
- 提供数据源连接测试功能
- 实现对Hive和Kingbase8的驱动接入

#### 1.3 ELT配置模块
- 定义数据迁移任务的数据结构
- 实现跨数据库数据传输功能
- 开发字段类型映射与转换机制
- 添加时间范围筛选条件设置
- 实现JOIN操作逻辑

#### 1.4 调度管理模块
- 集成任务调度器(APScheduler)
- 设计任务依赖关系表示方法
- 实现任务失败检测与重试机制
- 提供调度任务监控功能

### 2. 数据库设计概要

#### 2.1 用户表 (users)
- id: 主键
- username: 用户名
- password_hash: 密码哈希值
- email: 邮箱
- created_at: 创建时间

#### 2.2 数据源表 (data_sources)
- id: 主键
- name: 数据源名称
- type: 数据库类型
- connection_params: 连接参数(JSON格式)
- created_by: 创建用户ID
- created_at: 创建时间

#### 2.3 ELT任务表 (elt_tasks)
- id: 主键
- name: 任务名称
- source_db_id: 源数据库ID
- target_db_id: 目标数据库ID
- transformation_rules: 转换规则(JSON格式)
- schedule_config: 调度配置(JSON格式)
- created_by: 创建用户ID
- created_at: 创建时间
- updated_at: 更新时间

### 3. API接口概要

#### 3.1 用户认证相关
- POST /api/auth/register: 用户注册
- POST /api/auth/login: 用户登录
- POST /api/auth/logout: 用户登出
- GET /api/auth/profile: 获取用户信息

#### 3.2 数据源管理相关
- GET /api/data-sources: 获取所有数据源
- POST /api/data-sources: 创建新数据源
- PUT /api/data-sources/{id}: 更新数据源
- DELETE /api/data-sources/{id}: 删除数据源
- POST /api/data-sources/test-connection: 测试连接

#### 3.3 ELT任务管理相关
- GET /api/elt-tasks: 获取所有ELT任务
- POST /api/elt-tasks: 创建新ELT任务
- PUT /api/elt-tasks/{id}: 更新ELT任务
- DELETE /api/elt-tasks/{id}: 删除ELT任务
- POST /api/elt-tasks/{id}/execute: 执行ELT任务

#### 3.4 调度管理相关
- GET /api/schedules: 获取所有调度任务
- POST /api/schedules: 创建调度任务
- PUT /api/schedules/{id}: 更新调度任务
- DELETE /api/schedules/{id}: 删除调度任务

## 详细设计说明书

### 1. 后端详细设计

#### 1.1 项目结构
```
backend/
├── app.py                 # 应用入口
├── config.py             # 配置文件
├── models/               # 数据模型
│   ├── __init__.py
│   ├── user.py           # 用户模型
│   ├── data_source.py    # 数据源模型
│   └── elt_task.py       # ELT任务模型
├── routes/               # API路由
│   ├── __init__.py
│   ├── auth.py           # 认证路由
│   ├── data_sources.py   # 数据源路由
│   ├── elt_tasks.py      # ELT任务路由
│   └── schedules.py      # 调度路由
├── services/             # 业务逻辑
│   ├── __init__.py
│   ├── auth_service.py   # 认证服务
│   ├── db_connector.py   # 数据库连接服务
│   ├── elt_engine.py     # ELT引擎
│   └── scheduler.py      # 调度器
├── utils/                # 工具函数
│   ├── __init__.py
│   ├── validators.py     # 验证器
│   └── helpers.py        # 辅助函数
└── requirements.txt      # 依赖包列表
```

#### 1.2 核心模块设计

##### 1.2.1 用户认证模块详细设计
- 使用Flask-JWT-Extended实现JWT认证
- 用户密码使用werkzeug.security.hash_password进行加密
- 提供装饰器@token_required用于保护API端点
- 实现刷新令牌功能以增强安全性

##### 1.2.2 数据源管理模块详细设计
- 数据源模型包含连接参数的加密存储
- 实现通用数据库连接器基类，便于扩展新的数据库类型
- Hive连接器使用PyHive或impala-dbapi
- Kingbase8连接器使用psycopg2或适配的驱动
- 提供连接测试API验证配置正确性

##### 1.2.3 ELT引擎详细设计
- 实现数据抽取(Extract)功能，支持批量和增量抽取
- 实现数据转换(Transform)功能，包括字段映射、类型转换等
- 实现数据加载(Load)功能，支持覆盖、追加等不同加载策略
- 支持复杂查询语句生成，包括JOIN操作
- 提供事务管理确保数据一致性

##### 1.2.4 任务调度模块详细设计
- 使用APScheduler实现任务调度功能
- 支持Cron表达式、间隔调度、一次性任务等多种调度方式
- 实现任务依赖图解析，按依赖顺序执行任务
- 提供任务失败重试机制，可配置重试次数和间隔
- 记录任务执行日志，便于问题排查

### 2. 前端详细设计

#### 2.1 项目结构
```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── assets/           # 静态资源
│   ├── components/       # 公共组件
│   │   ├── Header.vue
│   │   ├── Sidebar.vue
│   │   └── ...
│   ├── views/            # 页面视图
│   │   ├── Login.vue
│   │   ├── Register.vue
│   │   ├── DataSourceManagement.vue
│   │   ├── ELTConfig.vue
│   │   └── ScheduleConfig.vue
│   ├── router/           # 路由配置
│   │   └── index.js
│   ├── store/            # Vuex状态管理
│   │   └── index.js
│   ├── api/              # API请求封装
│   │   ├── index.js
│   │   └── modules/
│   │       ├── auth.js
│   │       ├── dataSources.js
│   │       ├── eltTasks.js
│   │       └── schedules.js
│   ├── utils/            # 工具函数
│   │   └── request.js
│   ├── App.vue
│   └── main.js
├── package.json
└── vue.config.js
```

#### 2.2 页面设计

##### 2.2.1 登录注册页面
- 登录页面包含用户名/邮箱输入框、密码输入框、登录按钮
- 注册页面包含用户名、邮箱、密码、确认密码等字段
- 实现表单验证，包括非空验证、邮箱格式验证等
- 使用Axios调用后端API实现登录注册逻辑

##### 2.2.2 数据源管理页面
- 显示已配置的数据源列表
- 提供新增、编辑、删除数据源的功能
- 支持测试数据源连接的功能
- 表单包含数据库类型选择、连接参数输入等

##### 2.2.3 ELT配置页面
- 提供源数据库和目标数据库的选择
- 支持表选择和字段映射配置
- 实现时间范围选择功能
- 提供JOIN操作配置界面
- 支持预览转换规则的功能

##### 2.2.4 调度配置页面
- 显示所有调度任务列表
- 提供创建、编辑、删除调度任务的功能
- 实现调度时间配置（支持Cron表达式）
- 显示任务依赖关系图
- 显示任务执行历史和状态

### 3. 数据库表结构详细设计

#### 3.1 用户表 (users)
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.2 数据源表 (data_sources)
```sql
CREATE TABLE data_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,  -- 'hive', 'kingbase8', etc.
    connection_params TEXT NOT NULL,  -- JSON格式存储连接参数
    created_by INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users (id)
);
```

#### 3.3 ELT任务表 (elt_tasks)
```sql
CREATE TABLE elt_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    source_db_id INTEGER NOT NULL,
    target_db_id INTEGER NOT NULL,
    transformation_rules TEXT,  -- JSON格式存储转换规则
    join_conditions TEXT,       -- JSON格式存储JOIN条件
    time_filter TEXT,          -- JSON格式存储时间范围条件
    created_by INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_db_id) REFERENCES data_sources (id),
    FOREIGN KEY (target_db_id) REFERENCES data_sources (id),
    FOREIGN KEY (created_by) REFERENCES users (id)
);
```

#### 3.4 调度配置表 (schedules)
```sql
CREATE TABLE schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    schedule_type VARCHAR(20) NOT NULL,  -- 'cron', 'interval', 'date'
    schedule_config TEXT NOT NULL,      -- JSON格式存储调度配置
    dependencies TEXT,                  -- JSON格式存储依赖任务
    retry_count INTEGER DEFAULT 0,
    retry_interval INTEGER DEFAULT 300, -- 重试间隔（秒）
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES elt_tasks (id),
    FOREIGN KEY (created_by) REFERENCES users (id)
);
```

#### 3.5 任务执行记录表 (task_executions)
```sql
CREATE TABLE task_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    schedule_id INTEGER,
    status VARCHAR(20) NOT NULL,  -- 'running', 'success', 'failed', 'cancelled'
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    execution_log TEXT,           -- 执行日志
    error_message TEXT,           -- 错误信息
    FOREIGN KEY (task_id) REFERENCES elt_tasks (id),
    FOREIGN KEY (schedule_id) REFERENCES schedules (id)
);
```

## 前端HTML原型

### 1. 登录页面 (login.html)
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ELT系统 - 登录</title>
    <link rel="stylesheet" href="https://unpkg.com/element-ui/lib/theme-chalk/index.css">
    <script src="https://cdn.jsdelivr.net/npm/vue@2.6.14/dist/vue.js"></script>
    <script src="https://unpkg.com/element-ui/lib/index.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <style>
        body { margin: 0; padding: 0; background-color: #f0f2f5; }
        .login-container {
            width: 100vw;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .login-form {
            width: 400px;
            padding: 30px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
        }
        .logo {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo h2 {
            color: #409EFF;
        }
    </style>
</head>
<body>
    <div id="app">
        <div class="login-container">
            <el-card class="login-form">
                <div class="logo">
                    <h2>ELT数据管理系统</h2>
                </div>
                <el-form :model="loginForm" :rules="rules" ref="loginForm">
                    <el-form-item prop="username">
                        <el-input v-model="loginForm.username" placeholder="请输入用户名或邮箱" prefix-icon="el-icon-user"></el-input>
                    </el-form-item>
                    <el-form-item prop="password">
                        <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" prefix-icon="el-icon-lock"></el-input>
                    </el-form-item>
                    <el-form-item>
                        <el-button type="primary" @click="handleLogin" style="width: 100%;">登录</el-button>
                    </el-form-item>
                    <el-form-item>
                        <el-button @click="handleRegister" style="width: 100%;">注册</el-button>
                    </el-form-item>
                </el-form>
            </el-card>
        </div>
    </div>

    <script>
        new Vue({
            el: '#app',
            data() {
                return {
                    loginForm: {
                        username: '',
                        password: ''
                    },
                    rules: {
                        username: [
                            { required: true, message: '请输入用户名', trigger: 'blur' }
                        ],
                        password: [
                            { required: true, message: '请输入密码', trigger: 'blur' },
                            { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
                        ]
                    }
                }
            },
            methods: {
                handleLogin() {
                    this.$refs.loginForm.validate((valid) => {
                        if (valid) {
                            // 调用登录API
                            axios.post('/api/auth/login', this.loginForm)
                                .then(response => {
                                    localStorage.setItem('token', response.data.token);
                                    this.$message.success('登录成功');
                                    window.location.href = 'dashboard.html';
                                })
                                .catch(error => {
                                    this.$message.error('登录失败：' + error.response.data.message);
                                });
                        }
                    });
                },
                handleRegister() {
                    window.location.href = 'register.html';
                }
            }
        })
    </script>
</body>
</html>
```

### 2. 注册页面 (register.html)
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ELT系统 - 注册</title>
    <link rel="stylesheet" href="https://unpkg.com/element-ui/lib/theme-chalk/index.css">
    <script src="https://cdn.jsdelivr.net/npm/vue@2.6.14/dist/vue.js"></script>
    <script src="https://unpkg.com/element-ui/lib/index.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <style>
        body { margin: 0; padding: 0; background-color: #f0f2f5; }
        .register-container {
            width: 100vw;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .register-form {
            width: 400px;
            padding: 30px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
        }
        .logo {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo h2 {
            color: #409EFF;
        }
    </style>
</head>
<body>
    <div id="app">
        <div class="register-container">
            <el-card class="register-form">
                <div class="logo">
                    <h2>用户注册</h2>
                </div>
                <el-form :model="registerForm" :rules="rules" ref="registerForm">
                    <el-form-item prop="username">
                        <el-input v-model="registerForm.username" placeholder="请输入用户名" prefix-icon="el-icon-user"></el-input>
                    </el-form-item>
                    <el-form-item prop="email">
                        <el-input v-model="registerForm.email" placeholder="请输入邮箱地址" prefix-icon="el-icon-message"></el-input>
                    </el-form-item>
                    <el-form-item prop="password">
                        <el-input v-model="registerForm.password" type="password" placeholder="请输入密码" prefix-icon="el-icon-lock"></el-input>
                    </el-form-item>
                    <el-form-item prop="confirmPassword">
                        <el-input v-model="registerForm.confirmPassword" type="password" placeholder="请确认密码" prefix-icon="el-icon-lock"></el-input>
                    </el-form-item>
                    <el-form-item>
                        <el-button type="primary" @click="handleRegister" style="width: 100%;">注册</el-button>
                    </el-form-item>
                    <el-form-item>
                        <el-button @click="goToLogin" style="width: 100%;">已有账户？去登录</el-button>
                    </el-form-item>
                </el-form>
            </el-card>
        </div>
    </div>

    <script>
        new Vue({
            el: '#app',
            data() {
                const validatePass = (rule, value, callback) => {
                    if (value !== this.registerForm.password) {
                        callback(new Error('两次输入密码不一致!'));
                    } else {
                        callback();
                    }
                };
                return {
                    registerForm: {
                        username: '',
                        email: '',
                        password: '',
                        confirmPassword: ''
                    },
                    rules: {
                        username: [
                            { required: true, message: '请输入用户名', trigger: 'blur' },
                            { min: 3, max: 15, message: '长度在 3 到 15 个字符', trigger: 'blur' }
                        ],
                        email: [
                            { required: true, message: '请输入邮箱地址', trigger: 'blur' },
                            { type: 'email', message: '请输入正确的邮箱地址', trigger: ['blur', 'change'] }
                        ],
                        password: [
                            { required: true, message: '请输入密码', trigger: 'blur' },
                            { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
                        ],
                        confirmPassword: [
                            { required: true, message: '请再次输入密码', trigger: 'blur' },
                            { validator: validatePass, trigger: 'blur' }
                        ]
                    }
                }
            },
            methods: {
                handleRegister() {
                    this.$refs.registerForm.validate((valid) => {
                        if (valid) {
                            // 调用注册API
                            axios.post('/api/auth/register', this.registerForm)
                                .then(response => {
                                    this.$message.success('注册成功，请登录');
                                    window.location.href = 'login.html';
                                })
                                .catch(error => {
                                    this.$message.error('注册失败：' + error.response.data.message);
                                });
                        }
                    });
                },
                goToLogin() {
                    window.location.href = 'login.html';
                }
            }
        })
    </script>
</body>
</html>
```

### 3. 仪表板页面 (dashboard.html)
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ELT系统 - 仪表板</title>
    <link rel="stylesheet" href="https://unpkg.com/element-ui/lib/theme-chalk/index.css">
    <script src="https://cdn.jsdelivr.net/npm/vue@2.6.14/dist/vue.js"></script>
    <script src="https://unpkg.com/element-ui/lib/index.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <style>
        html, body { margin: 0; padding: 0; height: 100%; overflow: hidden; }
        .main-container {
            height: 100vh;
            display: flex;
        }
        .sidebar {
            width: 200px;
            background-color: #545c64;
        }
        .content {
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        .header {
            height: 60px;
            background-color: #fff;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 20px;
            box-shadow: 0 1px 4px rgba(0,21,41,.08);
        }
        .main-content {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background-color: #f0f2f5;
        }
    </style>
</head>
<body>
    <div id="app">
        <div class="main-container">
            <!-- 侧边栏 -->
            <el-aside class="sidebar">
                <el-menu
                    :default-active="$route.path"
                    class="el-menu-vertical"
                    background-color="#545c64"
                    text-color="#fff"
                    active-text-color="#ffd04b"
                    router="true"
                >
                    <el-menu-item index="/dashboard">
                        <i class="el-icon-menu"></i>
                        <span slot="title">仪表板</span>
                    </el-menu-item>
                    <el-submenu index="data-source">
                        <template slot="title">
                            <i class="el-icon-setting"></i>
                            <span>数据源管理</span>
                        </template>
                        <el-menu-item index="/data-source/list">数据源列表</el-menu-item>
                        <el-menu-item index="/data-source/add">添加数据源</el-menu-item>
                    </el-submenu>
                    <el-submenu index="elt-config">
                        <template slot="title">
                            <i class="el-icon-data-analysis"></i>
                            <span>ELT配置</span>
                        </template>
                        <el-menu-item index="/elt-task/list">任务列表</el-menu-item>
                        <el-menu-item index="/elt-task/create">创建任务</el-menu-item>
                    </el-submenu>
                    <el-submenu index="schedule-config">
                        <template slot="title">
                            <i class="el-icon-timer"></i>
                            <span>调度配置</span>
                        </template>
                        <el-menu-item index="/schedule/list">调度列表</el-menu-item>
                        <el-menu-item index="/schedule/create">创建调度</el-menu-item>
                    </el-submenu>
                </el-menu>
            </el-aside>

            <!-- 主内容区 -->
            <div class="content">
                <el-header class="header">
                    <h3>ELT数据管理系统</h3>
                    <div>
                        <el-dropdown>
                            <span class="el-dropdown-link">
                                用户名 <i class="el-icon-arrow-down el-icon--right"></i>
                            </span>
                            <el-dropdown-menu slot="dropdown">
                                <el-dropdown-item>个人中心</el-dropdown-item>
                                <el-dropdown-item @click.native="logout">退出登录</el-dropdown-item>
                            </el-dropdown-menu>
                        </el-dropdown>
                    </div>
                </el-header>

                <div class="main-content">
                    <h1>欢迎使用ELT数据管理系统</h1>
                    <p>这是一个用于管理数据源、配置ETL任务和调度的平台。</p>

                    <el-row :gutter="20" style="margin-top: 20px;">
                        <el-col :span="6">
                            <el-card class="box-card">
                                <div slot="header" class="clearfix">
                                    <span>数据源数量</span>
                                </div>
                                <div class="stat-number">0</div>
                            </el-card>
                        </el-col>
                        <el-col :span="6">
                            <el-card class="box-card">
                                <div slot="header" class="clearfix">
                                    <span>ELT任务数</span>
                                </div>
                                <div class="stat-number">0</div>
                            </el-card>
                        </el-col>
                        <el-col :span="6">
                            <el-card class="box-card">
                                <div slot="header" class="clearfix">
                                    <span>调度任务数</span>
                                </div>
                                <div class="stat-number">0</div>
                            </el-card>
                        </el-col>
                        <el-col :span="6">
                            <el-card class="box-card">
                                <div slot="header" class="clearfix">
                                    <span>最近执行</span>
                                </div>
                                <div class="stat-number">-</div>
                            </el-card>
                        </el-col>
                    </el-row>
                </div>
            </div>
        </div>
    </div>

    <script>
        new Vue({
            el: '#app',
            methods: {
                logout() {
                    localStorage.removeItem('token');
                    window.location.href = 'login.html';
                }
            }
        })
    </script>
</body>
</html>
```

### 4. 数据源管理页面 (data-source.html)
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ELT系统 - 数据源管理</title>
    <link rel="stylesheet" href="https://unpkg.com/element-ui/lib/theme-chalk/index.css">
    <script src="https://cdn.jsdelivr.net/npm/vue@2.6.14/dist/vue.js"></script>
    <script src="https://unpkg.com/element-ui/lib/index.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <style>
        html, body { margin: 0; padding: 0; height: 100%; }
        .main-container {
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .header {
            height: 60px;
            background-color: #fff;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 20px;
            box-shadow: 0 1px 4px rgba(0,21,41,.08);
        }
        .main-content {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background-color: #f0f2f5;
        }
        .data-source-form {
            width: 600px;
            margin: 0 auto;
        }
        .form-section {
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div id="app">
        <div class="main-container">
            <el-header class="header">
                <h3>数据源管理</h3>
                <div>
                    <el-button type="primary" @click="showAddForm">添加数据源</el-button>
                </div>
            </el-header>

            <div class="main-content">
                <el-table :data="dataSources" style="width: 100%">
                    <el-table-column prop="name" label="数据源名称" width="200"></el-table-column>
                    <el-table-column prop="type" label="类型" width="150">
                        <template slot-scope="scope">
                            <el-tag>{{ scope.row.type }}</el-tag>
                        </template>
                    </el-table-column>
                    <el-table-column prop="createdAt" label="创建时间" width="200"></el-table-column>
                    <el-table-column label="操作" width="250">
                        <template slot-scope="scope">
                            <el-button size="mini" @click="testConnection(scope.row)">测试连接</el-button>
                            <el-button size="mini" @click="editDataSource(scope.row)">编辑</el-button>
                            <el-button size="mini" type="danger" @click="deleteDataSource(scope.row)">删除</el-button>
                        </template>
                    </el-table-column>
                </el-table>

                <!-- 添加/编辑数据源对话框 -->
                <el-dialog :title="dialogTitle" :visible.sync="dialogVisible" width="600px">
                    <el-form :model="dataSourceForm" :rules="dataSourceRules" ref="dataSourceForm" label-width="120px">
                        <el-form-item label="数据源名称" prop="name">
                            <el-input v-model="dataSourceForm.name" placeholder="请输入数据源名称"></el-input>
                        </el-form-item>
                        <el-form-item label="数据库类型" prop="type">
                            <el-select v-model="dataSourceForm.type" placeholder="请选择数据库类型" style="width: 100%;">
                                <el-option label="Hive" value="hive"></el-option>
                                <el-option label="Kingbase8" value="kingbase8"></el-option>
                            </el-select>
                        </el-form-item>

                        <div class="form-section">
                            <h4>连接参数</h4>
                            <el-form-item label="主机地址" prop="host">
                                <el-input v-model="dataSourceForm.host" placeholder="请输入主机地址"></el-input>
                            </el-form-item>
                            <el-form-item label="端口" prop="port">
                                <el-input v-model.number="dataSourceForm.port" placeholder="请输入端口号"></el-input>
                            </el-form-item>
                            <el-form-item label="数据库名" prop="database">
                                <el-input v-model="dataSourceForm.database" placeholder="请输入数据库名"></el-input>
                            </el-form-item>
                            <el-form-item label="用户名" prop="username">
                                <el-input v-model="dataSourceForm.username" placeholder="请输入用户名"></el-input>
                            </el-form-item>
                            <el-form-item label="密码" prop="password">
                                <el-input v-model="dataSourceForm.password" type="password" placeholder="请输入密码"></el-input>
                            </el-form-item>
                        </div>
                    </el-form>
                    <span slot="footer" class="dialog-footer">
                        <el-button @click="dialogVisible = false">取 消</el-button>
                        <el-button type="primary" @click="submitDataSourceForm">确 定</el-button>
                    </span>
                </el-dialog>
            </div>
        </div>
    </div>

    <script>
        new Vue({
            el: '#app',
            data() {
                return {
                    dataSources: [
                        { id: 1, name: 'Hive生产环境', type: 'hive', createdAt: '2023-01-15 10:30:00' },
                        { id: 2, name: 'Kingbase开发库', type: 'kingbase8', createdAt: '2023-01-20 14:22:15' }
                    ],
                    dialogVisible: false,
                    isEdit: false,
                    dataSourceForm: {
                        name: '',
                        type: '',
                        host: '',
                        port: null,
                        database: '',
                        username: '',
                        password: ''
                    },
                    dataSourceRules: {
                        name: [
                            { required: true, message: '请输入数据源名称', trigger: 'blur' }
                        ],
                        type: [
                            { required: true, message: '请选择数据库类型', trigger: 'change' }
                        ],
                        host: [
                            { required: true, message: '请输入主机地址', trigger: 'blur' }
                        ],
                        port: [
                            { required: true, message: '请输入端口号', trigger: 'blur' },
                            { type: 'number', message: '端口号必须为数字' }
                        ],
                        database: [
                            { required: true, message: '请输入数据库名', trigger: 'blur' }
                        ],
                        username: [
                            { required: true, message: '请输入用户名', trigger: 'blur' }
                        ]
                    }
                }
            },
            computed: {
                dialogTitle() {
                    return this.isEdit ? '编辑数据源' : '添加数据源';
                }
            },
            methods: {
                showAddForm() {
                    this.isEdit = false;
                    this.dataSourceForm = {
                        name: '',
                        type: '',
                        host: '',
                        port: null,
                        database: '',
                        username: '',
                        password: ''
                    };
                    this.dialogVisible = true;
                },
                editDataSource(row) {
                    this.isEdit = true;
                    this.dataSourceForm = { ...row };
                    this.dialogVisible = true;
                },
                testConnection(row) {
                    this.$message.info(`正在测试${row.name}的连接...`);
                    // 模拟API调用
                    setTimeout(() => {
                        this.$message.success('连接成功！');
                    }, 1000);
                },
                deleteDataSource(row) {
                    this.$confirm(`确定要删除数据源 "${row.name}" 吗？`, '提示', {
                        confirmButtonText: '确定',
                        cancelButtonText: '取消',
                        type: 'warning'
                    }).then(() => {
                        this.dataSources = this.dataSources.filter(item => item.id !== row.id);
                        this.$message.success('删除成功！');
                    });
                },
                submitDataSourceForm() {
                    this.$refs.dataSourceForm.validate((valid) => {
                        if (valid) {
                            if (this.isEdit) {
                                // 编辑现有数据源
                                const index = this.dataSources.findIndex(item => item.id === this.dataSourceForm.id);
                                if (index !== -1) {
                                    this.dataSources.splice(index, 1, { ...this.dataSourceForm });
                                }
                            } else {
                                // 添加新数据源
                                this.dataSources.push({
                                    ...this.dataSourceForm,
                                    id: this.dataSources.length + 1,
                                    createdAt: new Date().toLocaleString()
                                });
                            }

                            this.dialogVisible = false;
                            this.$message.success(this.isEdit ? '更新成功！' : '添加成功！');
                        }
                    });
                }
            }
        })
    </script>
</body>
</html>
```

### 5. ELT任务配置页面 (elt-config.html)
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ELT系统 - ELT任务配置</title>
    <link rel="stylesheet" href="https://unpkg.com/element-ui/lib/theme-chalk/index.css">
    <script src="https://cdn.jsdelivr.net/npm/vue@2.6.14/dist/vue.js"></script>
    <script src="https://unpkg.com/element-ui/lib/index.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <style>
        html, body { margin: 0; padding: 0; height: 100%; }
        .main-container {
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .header {
            height: 60px;
            background-color: #fff;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 20px;
            box-shadow: 0 1px 4px rgba(0,21,41,.08);
        }
        .main-content {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background-color: #f0f2f5;
        }
        .config-panel {
            background: white;
            padding: 20px;
            border-radius: 4px;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
        }
        .step-title {
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }
    </style>
</head>
<body>
    <div id="app">
        <div class="main-container">
            <el-header class="header">
                <h3>ELT任务配置</h3>
                <div>
                    <el-button type="primary" @click="saveTask">保存任务</el-button>
                </div>
            </el-header>

            <div class="main-content">
                <el-steps :active="activeStep" finish-status="success" simple style="margin-bottom: 20px;">
                    <el-step title="基本信息"></el-step>
                    <el-step title="数据源选择"></el-step>
                    <el-step title="字段映射"></el-step>
                    <el-step title="转换规则"></el-step>
                    <el-step title="时间过滤"></el-step>
                </el-steps>

                <div class="config-panel" v-if="activeStep === 0">
                    <div class="step-title">任务基本信息</div>
                    <el-form :model="taskForm" :rules="basicInfoRules" ref="basicInfoForm" label-width="120px">
                        <el-form-item label="任务名称" prop="name">
                            <el-input v-model="taskForm.name" placeholder="请输入任务名称"></el-input>
                        </el-form-item>
                        <el-form-item label="任务描述" prop="description">
                            <el-input v-model="taskForm.description" type="textarea" placeholder="请输入任务描述"></el-input>
                        </el-form-item>
                    </el-form>
                    <div style="text-align: center; margin-top: 20px;">
                        <el-button @click="previousStep" v-if="activeStep > 0">上一步</el-button>
                        <el-button type="primary" @click="nextStep">下一步</el-button>
                    </div>
                </div>

                <div class="config-panel" v-if="activeStep === 1">
                    <div class="step-title">数据源选择</div>
                    <el-form :model="taskForm" label-width="120px">
                        <el-form-item label="源数据源" prop="sourceDbId">
                            <el-select v-model="taskForm.sourceDbId" placeholder="请选择源数据源" style="width: 100%;">
                                <el-option v-for="ds in dataSources" :key="ds.id" :label="ds.name" :value="ds.id"></el-option>
                            </el-select>
                        </el-form-item>
                        <el-form-item label="目标数据源" prop="targetDbId">
                            <el-select v-model="taskForm.targetDbId" placeholder="请选择目标数据源" style="width: 100%;">
                                <el-option v-for="ds in dataSources" :key="ds.id" :label="ds.name" :value="ds.id"></el-option>
                            </el-select>
                        </el-form-item>
                        <el-form-item label="源表" prop="sourceTable">
                            <el-input v-model="taskForm.sourceTable" placeholder="请输入源表名"></el-input>
                        </el-form-item>
                        <el-form-item label="目标表" prop="targetTable">
                            <el-input v-model="taskForm.targetTable" placeholder="请输入目标表名"></el-input>
                        </el-form-item>
                    </el-form>
                    <div style="text-align: center; margin-top: 20px;">
                        <el-button @click="previousStep">上一步</el-button>
                        <el-button type="primary" @click="nextStep">下一步</el-button>
                    </div>
                </div>

                <div class="config-panel" v-if="activeStep === 2">
                    <div class="step-title">字段映射</div>
                    <el-table :data="fieldMappings" style="width: 100%">
                        <el-table-column prop="sourceField" label="源字段" width="200">
                            <template slot-scope="scope">
                                <el-input v-model="scope.row.sourceField" placeholder="源字段名"></el-input>
                            </template>
                        </el-table-column>
                        <el-table-column label="转换操作" width="150">
                            <template slot-scope="scope">
                                <el-select v-model="scope.row.transformation" placeholder="选择转换" style="width: 100%;">
                                    <el-option label="无转换" value="none"></el-option>
                                    <el-option label="类型转换" value="type_conversion"></el-option>
                                    <el-option label="字符串处理" value="string_process"></el-option>
                                </el-select>
                            </template>
                        </el-table-column>
                        <el-table-column prop="targetField" label="目标字段" width="200">
                            <template slot-scope="scope">
                                <el-input v-model="scope.row.targetField" placeholder="目标字段名"></el-input>
                            </template>
                        </el-table-column>
                        <el-table-column label="操作" width="100">
                            <template slot-scope="scope">
                                <el-button size="mini" type="danger" @click="removeFieldMapping(scope.$index)">删除</el-button>
                            </template>
                        </el-table-column>
                    </el-table>
                    <div style="margin-top: 15px;">
                        <el-button @click="addFieldMapping" icon="el-icon-plus">添加字段映射</el-button>
                    </div>
                    <div style="text-align: center; margin-top: 20px;">
                        <el-button @click="previousStep">上一步</el-button>
                        <el-button type="primary" @click="nextStep">下一步</el-button>
                    </div>
                </div>

                <div class="config-panel" v-if="activeStep === 3">
                    <div class="step-title">转换规则</div>
                    <el-form label-width="120px">
                        <el-form-item label="JOIN操作">
                            <el-switch v-model="enableJoin"></el-switch>
                        </el-form-item>

                        <div v-if="enableJoin">
                            <el-form-item label="关联表">
                                <el-input v-model="joinConfig.joinTable" placeholder="请输入关联表名"></el-input>
                            </el-form-item>
                            <el-form-item label="关联条件">
                                <el-input v-model="joinConfig.joinCondition" placeholder="例如: t1.id = t2.ref_id"></el-input>
                            </el-form-item>
                            <el-form-item label="JOIN类型">
                                <el-select v-model="joinConfig.joinType" style="width: 100%;">
                                    <el-option label="INNER JOIN" value="inner"></el-option>
                                    <el-option label="LEFT JOIN" value="left"></el-option>
                                    <el-option label="RIGHT JOIN" value="right"></el-option>
                                </el-select>
                            </el-form-item>
                        </div>

                        <el-form-item label="数据过滤">
                            <el-input v-model="taskForm.filters" type="textarea" :rows="4" placeholder="请输入SQL WHERE条件"></el-input>
                        </el-form-item>
                    </el-form>
                    <div style="text-align: center; margin-top: 20px;">
                        <el-button @click="previousStep">上一步</el-button>
                        <el-button type="primary" @click="nextStep">下一步</el-button>
                    </div>
                </div>

                <div class="config-panel" v-if="activeStep === 4">
                    <div class="step-title">时间范围过滤</div>
                    <el-form :model="timeFilter" label-width="120px">
                        <el-form-item label="启用时间过滤">
                            <el-switch v-model="timeFilter.enabled"></el-switch>
                        </el-form-item>

                        <div v-if="timeFilter.enabled">
                            <el-form-item label="时间字段">
                                <el-input v-model="timeFilter.field" placeholder="请输入时间字段名，如：create_date"></el-input>
                            </el-form-item>
                            <el-form-item label="开始时间">
                                <el-date-picker
                                    v-model="timeFilter.startTime"
                                    type="datetime"
                                    placeholder="选择开始时间">
                                </el-date-picker>
                            </el-form-item>
                            <el-form-item label="结束时间">
                                <el-date-picker
                                    v-model="timeFilter.endTime"
                                    type="datetime"
                                    placeholder="选择结束时间">
                                </el-date-picker>
                            </el-form-item>
                            <el-form-item label="时间条件">
                                <el-radio-group v-model="timeFilter.condition">
                                    <el-radio label="between">在时间范围内</el-radio>
                                    <el-radio label="after">晚于指定时间</el-radio>
                                    <el-radio label="before">早于指定时间</el-radio>
                                </el-radio-group>
                            </el-form-item>
                        </div>
                    </el-form>
                    <div style="text-align: center; margin-top: 20px;">
                        <el-button @click="previousStep">上一步</el-button>
                        <el-button type="primary" @click="finishConfiguration">完成配置</el-button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        new Vue({
            el: '#app',
            data() {
                return {
                    activeStep: 0,
                    dataSources: [
                        { id: 1, name: 'Hive生产环境' },
                        { id: 2, name: 'Kingbase开发库' }
                    ],
                    taskForm: {
                        name: '',
                        description: '',
                        sourceDbId: '',
                        targetDbId: '',
                        sourceTable: '',
                        targetTable: '',
                        filters: ''
                    },
                    basicInfoRules: {
                        name: [
                            { required: true, message: '请输入任务名称', trigger: 'blur' }
                        ]
                    },
                    fieldMappings: [
                        { sourceField: '', transformation: 'none', targetField: '' }
                    ],
                    enableJoin: false,
                    joinConfig: {
                        joinTable: '',
                        joinCondition: '',
                        joinType: 'inner'
                    },
                    timeFilter: {
                        enabled: false,
                        field: '',
                        startTime: null,
                        endTime: null,
                        condition: 'between'
                    }
                }
            },
            methods: {
                nextStep() {
                    if (this.activeStep === 0) {
                        this.$refs.basicInfoForm.validate((valid) => {
                            if (valid) {
                                this.activeStep++;
                            }
                        });
                    } else {
                        this.activeStep++;
                    }
                },
                previousStep() {
                    if (this.activeStep > 0) {
                        this.activeStep--;
                    }
                },
                addFieldMapping() {
                    this.fieldMappings.push({ sourceField: '', transformation: 'none', targetField: '' });
                },
                removeFieldMapping(index) {
                    if (this.fieldMappings.length > 1) {
                        this.fieldMappings.splice(index, 1);
                    }
                },
                finishConfiguration() {
                    this.$message.success('任务配置完成！');
                },
                saveTask() {
                    this.$message.success('任务已保存！');
                }
            }
        })
    </script>
</body>
</html>
```

这些原型展示了系统的前端界面，包括：

1. 登录页面 - 实现用户认证功能
2. 注册页面 - 实现新用户注册功能
3. 仪表板页面 - 主界面，包含导航菜单和统计信息
4. 数据源管理页面 - 用于配置和管理不同的数据源
5. ELT任务配置页面 - 多步骤向导，用于配置数据转换任务

以上原型均使用Vue.js和Element UI构建，符合现代Web应用的设计标准。