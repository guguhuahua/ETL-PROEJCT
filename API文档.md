# API接口文档

## ETL系统API接口文档

### 1. 认证相关接口

#### 1.1 用户注册
- **接口地址**: `POST /api/auth/register`
- **请求参数**:
  ```json
  {
    "username": "用户名",
    "email": "邮箱地址",
    "password": "密码"
  }
  ```
- **响应参数**:
  ```json
  {
    "message": "注册成功"
  }
  ```
- **错误响应**:
  - 400: 用户名或邮箱已被使用

#### 1.2 用户登录
- **接口地址**: `POST /api/auth/login`
- **请求参数**:
  ```json
  {
    "username": "用户名",
    "password": "密码"
  }
  ```
- **响应参数**:
  ```json
  {
    "access_token": "JWT访问令牌",
    "user": {
      "id": "用户ID",
      "username": "用户名",
      "email": "邮箱"
    }
  }
  ```
- **错误响应**:
  - 401: 用户名或密码错误

#### 1.3 获取用户信息
- **接口地址**: `GET /api/auth/profile`
- **请求头**: `Authorization: Bearer {token}`
- **响应参数**:
  ```json
  {
    "id": "用户ID",
    "username": "用户名",
    "email": "邮箱"
  }
  ```

### 2. 数据源管理接口

#### 2.1 获取所有数据源
- **接口地址**: `GET /api/data-sources`
- **请求头**: `Authorization: Bearer {token}`
- **响应参数**:
  ```json
  [
    {
      "id": "数据源ID",
      "name": "数据源名称",
      "type": "数据源类型(hive, kingbase8, mysql, postgresql)",
      "created_at": "创建时间",
      "updated_at": "更新时间"
    }
  ]
  ```

#### 2.2 创建数据源
- **接口地址**: `POST /api/data-sources`
- **请求头**: `Authorization: Bearer {token}`
- **请求参数**:
  ```json
  {
    "name": "数据源名称",
    "type": "数据源类型",
    "connection_params": {
      "host": "主机地址",
      "port": "端口号",
      "database": "数据库名",
      "username": "用户名",
      "password": "密码"
    }
  }
  ```
- **响应参数**:
  ```json
  {
    "id": "数据源ID",
    "name": "数据源名称",
    "type": "数据源类型",
    "message": "数据源创建成功"
  }
  ```

#### 2.3 更新数据源
- **接口地址**: `PUT /api/data-sources/{id}`
- **请求头**: `Authorization: Bearer {token}`
- **请求参数**:
  ```json
  {
    "name": "数据源名称",
    "type": "数据源类型",
    "connection_params": {
      "host": "主机地址",
      "port": "端口号",
      "database": "数据库名",
      "username": "用户名",
      "password": "密码"
    }
  }
  ```
- **响应参数**:
  ```json
  {
    "id": "数据源ID",
    "name": "数据源名称",
    "type": "数据源类型",
    "message": "数据源更新成功"
  }
  ```

#### 2.4 删除数据源
- **接口地址**: `DELETE /api/data-sources/{id}`
- **请求头**: `Authorization: Bearer {token}`
- **响应参数**:
  ```json
  {
    "message": "数据源删除成功"
  }
  ```

#### 2.5 测试数据源连接
- **接口地址**: `POST /api/data-sources/test-connection`
- **请求头**: `Authorization: Bearer {token}`
- **请求参数**:
  ```json
  {
    "type": "数据源类型",
    "connection_params": {
      "host": "主机地址",
      "port": "端口号",
      "database": "数据库名",
      "username": "用户名",
      "password": "密码"
    }
  }
  ```
- **响应参数**:
  ```json
  {
    "message": "连接测试成功"
  }
  ```

### 3. ELT任务管理接口

#### 3.1 获取所有ELT任务
- **接口地址**: `GET /api/elt-tasks`
- **请求头**: `Authorization: Bearer {token}`
- **响应参数**:
  ```json
  [
    {
      "id": "任务ID",
      "name": "任务名称",
      "description": "任务描述",
      "source_type": "源类型(table, sql_query)",
      "source_db_id": "源数据库ID",
      "target_db_id": "目标数据库ID",
      "source_table": "源表名(仅table模式)",
      "target_table": "目标表名",
      "source_sql": "源SQL(仅sql_query模式)",
      "created_at": "创建时间",
      "updated_at": "更新时间"
    }
  ]
  ```

#### 3.2 创建ELT任务
- **接口地址**: `POST /api/elt-tasks`
- **请求头**: `Authorization: Bearer {token}`
- **请求参数**:
  ```json
  {
    "name": "任务名称",
    "description": "任务描述",
    "source_db_id": "源数据库ID",
    "target_db_id": "目标数据库ID",
    "source_type": "源类型(table, sql_query)",
    "source_table": "源表名(仅table模式)",
    "target_table": "目标表名",
    "source_sql": "源SQL(仅sql_query模式)",
    "transformation_rules": [], // 转换规则
    "join_conditions": {}, // JOIN条件
    "time_filter": {} // 时间过滤条件
  }
  ```
- **响应参数**:
  ```json
  {
    "id": "任务ID",
    "name": "任务名称",
    "message": "ELT任务创建成功"
  }
  ```

#### 3.3 更新ELT任务
- **接口地址**: `PUT /api/elt-tasks/{id}`
- **请求头**: `Authorization: Bearer {token}`
- **请求参数**: 同创建任务
- **响应参数**:
  ```json
  {
    "id": "任务ID",
    "name": "任务名称",
    "message": "ELT任务更新成功"
  }
  ```

#### 3.4 删除ELT任务
- **接口地址**: `DELETE /api/elt-tasks/{id}`
- **请求头**: `Authorization: Bearer {token}`
- **响应参数**:
  ```json
  {
    "message": "ELT任务删除成功"
  }
  ```

#### 3.5 执行ELT任务
- **接口地址**: `POST /api/elt-tasks/{id}/execute`
- **请求头**: `Authorization: Bearer {token}`
- **响应参数**:
  ```json
  {
    "execution_id": "执行ID",
    "message": "任务执行成功",
    "details": {} // 执行详情
  }
  ```
- **错误响应**:
  ```json
  {
    "execution_id": "执行ID",
    "error": "错误信息"
  }
  ```

#### 3.6 预览SQL查询结果
- **接口地址**: `POST /api/elt-tasks/{id}/preview-sql`
- **请求头**: `Authorization: Bearer {token}`
- **请求参数**:
  ```json
  {
    "sql": "要预览的SQL语句(可选，不提供则使用任务中的SQL)"
  }
  ```
- **响应参数**:
  ```json
  {
    "columns": [ // 列信息
      {
        "name": "列名",
        "type": "数据类型",
        "example": "示例值"
      }
    ],
    "preview_data": [ // 预览数据
      // 最多5条记录
    ],
    "total_count": "总记录数"
  }
  ```

### 4. 调度管理接口

#### 4.1 获取所有调度任务
- **接口地址**: `GET /api/schedules`
- **请求头**: `Authorization: Bearer {token}`
- **响应参数**:
  ```json
  [
    {
      "id": "调度ID",
      "task_id": "关联任务ID",
      "name": "调度名称",
      "schedule_type": "调度类型(cron, interval, date)",
      "schedule_config": "调度配置",
      "dependencies": "依赖关系",
      "retry_count": "重试次数",
      "retry_interval": "重试间隔",
      "is_active": "是否激活",
      "created_at": "创建时间",
      "updated_at": "更新时间"
    }
  ]
  ```

#### 4.2 创建调度任务
- **接口地址**: `POST /api/schedules`
- **请求头**: `Authorization: Bearer {token}`
- **请求参数**:
  ```json
  {
    "task_id": "关联任务ID",
    "name": "调度名称",
    "schedule_type": "调度类型(cron, interval, date)",
    "schedule_config": {
      // 根据类型不同配置不同
      // cron: { "cron_expression": "0 9 * * *" }
      // interval: { "interval_seconds": 3600 }
      // date: { "run_time": "2023-01-01T10:00:00Z" }
    },
    "dependencies": [], // 依赖任务ID数组
    "retry_count": 3,
    "retry_interval": 300,
    "is_active": true
  }
  ```
- **响应参数**:
  ```json
  {
    "id": "调度ID",
    "name": "调度名称",
    "message": "调度任务创建成功"
  }
  ```

#### 4.3 更新调度任务
- **接口地址**: `PUT /api/schedules/{id}`
- **请求头**: `Authorization: Bearer {token}`
- **请求参数**: 同创建调度
- **响应参数**:
  ```json
  {
    "id": "调度ID",
    "name": "调度名称",
    "message": "调度任务更新成功"
  }
  ```

#### 4.4 删除调度任务
- **接口地址**: `DELETE /api/schedules/{id}`
- **请求头**: `Authorization: Bearer {token}`
- **响应参数**:
  ```json
  {
    "message": "调度任务删除成功"
  }
  ```

#### 4.5 启用/禁用调度
- **接口地址**: `POST /api/schedules/{id}/toggle`
- **请求头**: `Authorization: Bearer {token}`
- **响应参数**:
  ```json
  {
    "message": "调度已激活/已暂停",
    "schedule": {
      "id": "调度ID",
      "is_active": true/false
    }
  }
  ```

### 5. 任务执行记录接口

#### 5.1 获取任务执行记录
- **接口地址**: `GET /api/task-executions`
- **请求头**: `Authorization: Bearer {token}`
- **查询参数**:
  - `task_id`: 任务ID(可选)
  - `status`: 状态过滤(可选)
  - `page`: 页码(默认1)
  - `per_page`: 每页数量(默认20)
- **响应参数**:
  ```json
  {
    "executions": [
      {
        "id": "执行记录ID",
        "task_id": "任务ID",
        "task_name": "任务名称",
        "schedule_id": "调度ID(如果是调度执行)",
        "status": "执行状态(running, success, failed, cancelled)",
        "start_time": "开始时间",
        "end_time": "结束时间",
        "processed_rows": "处理行数",
        "error_message": "错误信息(如果失败)"
      }
    ],
    "total": "总数量",
    "pages": "总页数",
    "current_page": "当前页"
  }
  ```

#### 5.2 获取执行统计
- **接口地址**: `GET /api/task-executions/stats`
- **请求头**: `Authorization: Bearer {token}`
- **响应参数**:
  ```json
  {
    "total_executions": "总执行次数",
    "success_count": "成功次数",
    "failed_count": "失败次数",
    "running_count": "运行中次数",
    "total_processed_rows": "总处理行数"
  }
  ```

---

## 错误响应格式

所有接口在发生错误时返回统一格式：

```json
{
  "error": "错误信息描述"
}
```

常见HTTP状态码：
- `400`: 请求参数错误
- `401`: 未授权（未登录或Token过期）
- `403`: 禁止访问
- `404`: 资源不存在
- `500`: 服务器内部错误

---

## 数据库表结构

### users 表
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### data_sources 表
```sql
CREATE TABLE data_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    connection_params TEXT NOT NULL,
    created_by INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users (id)
);
```

### elt_tasks 表
```sql
CREATE TABLE elt_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    source_type VARCHAR(20) DEFAULT 'table',
    source_db_id INTEGER NOT NULL,
    target_db_id INTEGER NOT NULL,
    source_table VARCHAR(100),
    target_table VARCHAR(100) NOT NULL,
    source_sql TEXT,
    transformation_rules TEXT,
    join_conditions TEXT,
    time_filter TEXT,
    created_by INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_db_id) REFERENCES data_sources (id),
    FOREIGN KEY (target_db_id) REFERENCES data_sources (id),
    FOREIGN KEY (created_by) REFERENCES users (id)
);
```

### schedules 表
```sql
CREATE TABLE schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    schedule_type VARCHAR(20) NOT NULL,
    schedule_config TEXT NOT NULL,
    dependencies TEXT,
    retry_count INTEGER DEFAULT 0,
    retry_interval INTEGER DEFAULT 300,
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES elt_tasks (id),
    FOREIGN KEY (created_by) REFERENCES users (id)
);
```

### task_executions 表
```sql
CREATE TABLE task_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    schedule_id INTEGER,
    status VARCHAR(20) NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    processed_rows INTEGER DEFAULT 0,
    execution_log TEXT,
    error_message TEXT,
    FOREIGN KEY (task_id) REFERENCES elt_tasks (id),
    FOREIGN KEY (schedule_id) REFERENCES schedules (id)
);
```

---

## 运行说明

### 后端启动
```bash
cd backend
pip install -r requirements.txt
python app.py
```
后端服务将在 `http://localhost:5000` 启动

### 前端启动
```bash
cd frontend
npm install
npm run serve
```
前端服务将在 `http://localhost:8080` 启动

---

## 技术栈

- **前端**: Vue.js 3.x + Element Plus + Axios + Pinia + Vue Router
- **后端**: Flask 2.x + SQLAlchemy + Flask-JWT-Extended + APScheduler
- **数据库**: SQLite 3.x
- **任务调度**: APScheduler
- **支持的数据库连接**: Hive (PyHive), Kingbase8 (psycopg2)