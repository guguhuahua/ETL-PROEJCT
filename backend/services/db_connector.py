"""
Database Connector Service
Provides connectors for various database types
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class BaseConnector(ABC):
    """Base class for database connectors"""

    def __init__(self, connection_params: Dict[str, Any]):
        self.connection_params = connection_params
        self.connection = None

    @abstractmethod
    def connect(self):
        """Establish database connection"""
        pass

    @abstractmethod
    def disconnect(self):
        """Close database connection"""
        pass

    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """Test database connection"""
        pass

    @abstractmethod
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """Execute a query and return results"""
        pass

    @abstractmethod
    def get_tables(self) -> List[str]:
        """Get list of tables"""
        pass

    @abstractmethod
    def get_columns(self, table_name: str) -> List[Dict]:
        """Get columns for a table"""
        pass

    @abstractmethod
    def insert_data(self, table_name: str, data: List[Dict]) -> int:
        """Insert data into table"""
        pass

    def truncate_table(self, table_name: str) -> bool:
        """Truncate table (clear all data). Override in subclasses if needed."""
        try:
            conn = self.connect()
            if not conn:
                return False
            cursor = conn.cursor()
            cursor.execute(f"TRUNCATE TABLE {table_name}")
            conn.commit()
            cursor.close()
            self.disconnect()
            return True
        except Exception as e:
            logger.error(f"Failed to truncate table {table_name}: {e}")
            raise

    def delete_all_data(self, table_name: str) -> int:
        """Delete all data from table (alternative to truncate)."""
        try:
            conn = self.connect()
            if not conn:
                return 0
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {table_name}")
            deleted_count = cursor.rowcount
            conn.commit()
            cursor.close()
            self.disconnect()
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to delete data from {table_name}: {e}")
            raise


class HiveConnector(BaseConnector):
    """Hive database connector"""

    def __init__(self, connection_params: Dict[str, Any]):
        super().__init__(connection_params)
        self.host = connection_params.get('host', 'localhost')
        self.port = connection_params.get('port', 10000)
        self.database = connection_params.get('database', 'default')
        self.username = connection_params.get('username', '')
        self.password = connection_params.get('password', '')
        self.auth = connection_params.get('auth', 'NONE')

    def connect(self):
        """Connect to Hive"""
        try:
            from pyhive import hive

            conn_params = {
                'host': self.host,
                'port': self.port,
                'database': self.database,
            }

            if self.auth == 'KERBEROS':
                conn_params['auth'] = 'KERBEROS'
                if self.username:
                    conn_params['kerberos_service_name'] = self.username
            elif self.auth == 'LDAP':
                conn_params['auth'] = 'LDAP'
                conn_params['username'] = self.username
                if self.password:
                    conn_params['password'] = self.password
            elif self.auth == 'CUSTOM':
                conn_params['auth'] = 'CUSTOM'
                conn_params['username'] = self.username
                if self.password:
                    conn_params['password'] = self.password
            elif self.auth == 'PLAIN':
                conn_params['auth'] = 'PLAIN'
                conn_params['username'] = self.username
            elif self.auth == 'NOSASL':
                conn_params['auth'] = 'NOSASL'
            else:
                if self.username:
                    conn_params['username'] = self.username

            self.connection = hive.Connection(**conn_params)
            return self.connection

        except ImportError as e:
            raise ImportError(f"请安装 PyHive: pip install pyhive thrift {e}")
        except Exception as e:
            logger.error(f"Failed to connect to Hive: {e}")
            raise

    def disconnect(self):
        """Disconnect from Hive"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def test_connection(self) -> Dict[str, Any]:
        """Test Hive connection"""
        try:
            conn = self.connect()
            if conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1')
                cursor.fetchall()  # 读取结果
                cursor.close()
                self.disconnect()
                return {'success': True, 'message': 'Hive 连接成功'}
            else:
                return {'success': True, 'message': 'Connection successful (mock mode)'}
        except ImportError as e:
            return {'success': False, 'error': f'缺少依赖: {str(e)}'}
        except Exception as e:
            error_msg = str(e)
            # 友好化错误信息
            if 'LDAP' in error_msg and 'INVALID_CREDENTIALS' in error_msg:
                return {
                    'success': False,
                    'error': 'LDAP认证失败：用户名或密码错误，或用户不存在'
                }
            elif 'AuthenticationException' in error_msg:
                return {
                    'success': False,
                    'error': f'认证失败：{error_msg}'
                }
            return {'success': False, 'error': error_msg}

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """Execute Hive query"""
        try:
            conn = self.connect()
            if not conn:
                return []

            cursor = conn.cursor()
            logger.info(f"Executing Hive query: {query[:200]}..." if len(query) > 200 else f"Executing Hive query: {query}")
            cursor.execute(query)

            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            results = []

            # 分批获取数据
            batch_size = 10000
            total_rows = 0
            while True:
                rows = cursor.fetchmany(batch_size)
                if not rows:
                    break
                for row in rows:
                    results.append(dict(zip(columns, row)))
                total_rows += len(rows)
                logger.info(f"Fetched {total_rows} rows...")

            logger.info(f"Query completed, total {total_rows} rows fetched")
            cursor.close()
            self.disconnect()
            return results
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

    def get_tables(self) -> List[str]:
        """Get Hive tables"""
        try:
            results = self.execute_query("SHOW TABLES")
            return [list(r.values())[0] for r in results]
        except Exception:
            return []

    def get_columns(self, table_name: str) -> List[Dict]:
        """Get Hive table columns"""
        try:
            results = self.execute_query(f"DESCRIBE {table_name}")
            columns = []
            for r in results:
                col_name = list(r.values())[0]
                col_type = list(r.values())[1] if len(r) > 1 else 'string'
                if col_name and not col_name.startswith('#'):
                    columns.append({
                        'name': col_name,
                        'type': col_type
                    })
            return columns
        except Exception:
            return []

    def insert_data(self, table_name: str, data: List[Dict]) -> int:
        """Insert data into Hive table"""
        # Hive typically uses LOAD DATA or INSERT statements
        raise NotImplementedError("Hive insert requires specific implementation")


class KingbaseConnector(BaseConnector):
    """Kingbase8 database connector"""

    def __init__(self, connection_params: Dict[str, Any]):
        super().__init__(connection_params)
        self.host = connection_params.get('host', 'localhost')
        self.port = connection_params.get('port', 54321)
        self.database = connection_params.get('database', 'test')
        self.username = connection_params.get('username', '')
        self.password = connection_params.get('password', '')

    def connect(self):
        """Connect to Kingbase"""
        try:
            import psycopg2
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.username,
                password=self.password
            )
            return self.connection
        except ImportError:
            logger.warning("psycopg2 not installed, using mock connector")
            return None
        except Exception as e:
            logger.error(f"Failed to connect to Kingbase: {e}")
            raise

    def disconnect(self):
        """Disconnect from Kingbase"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def test_connection(self) -> Dict[str, Any]:
        """Test Kingbase connection"""
        try:
            conn = self.connect()
            if conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1')
                cursor.close()
                self.disconnect()
                return {'success': True, 'message': 'Connection successful'}
            else:
                return {'success': True, 'message': 'Connection successful (mock mode)'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """Execute Kingbase query"""
        try:
            conn = self.connect()
            if not conn:
                return []

            cursor = conn.cursor()
            cursor.execute(query, params)

            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            cursor.close()
            self.disconnect()
            return results
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

    def get_tables(self) -> List[str]:
        """Get Kingbase tables from all schemas"""
        query = """
        SELECT table_schema || '.' || table_name as full_name, table_name
        FROM information_schema.tables
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema', 'sys', 'pg_toast')
        ORDER BY table_schema, table_name
        """
        try:
            conn = self.connect()
            if not conn:
                return []
            cursor = conn.cursor()
            cursor.execute(query)
            tables = []
            for row in cursor.fetchall():
                # 返回 schema.table 格式
                tables.append(row[0])
            cursor.close()
            self.disconnect()
            return tables
        except Exception as e:
            logger.error(f"Failed to get tables: {e}")
            return []

    def get_columns(self, table_name: str) -> List[Dict]:
        """Get Kingbase table columns, supports schema.table format"""
        # 解析 schema 和 table
        if '.' in table_name:
            schema, table = table_name.split('.', 1)
        else:
            schema = 'public'
            table = table_name

        query = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = %s AND table_schema = %s
        ORDER BY ordinal_position
        """
        try:
            conn = self.connect()
            if not conn:
                return []
            cursor = conn.cursor()
            cursor.execute(query, (table, schema))
            columns = []
            for row in cursor.fetchall():
                columns.append({
                    'name': row[0],
                    'type': row[1],
                    'nullable': row[2] == 'YES'
                })
            cursor.close()
            self.disconnect()
            return columns
        except Exception as e:
            logger.error(f"Failed to get columns: {e}")
            return []

    def insert_data(self, table_name: str, data: List[Dict]) -> int:
        """Insert data into Kingbase table with batch processing"""
        if not data:
            return 0

        conn = self.connect()
        if not conn:
            return 0

        cursor = conn.cursor()
        columns = list(data[0].keys())
        placeholders = ', '.join(['%s'] * len(columns))
        query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"

        # 批量插入，每次插入1000条
        batch_size = 1000
        total_count = 0

        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            values_list = [[row.get(col) for col in columns] for row in batch]
            cursor.executemany(query, values_list)
            total_count += len(batch)
            logger.info(f"Inserted {total_count}/{len(data)} rows...")

        conn.commit()
        cursor.close()
        self.disconnect()
        logger.info(f"Batch insert completed, total {total_count} rows")
        return total_count


def get_connector(db_type: str, connection_params: Dict[str, Any]) -> BaseConnector:
    """Factory function to get appropriate connector"""
    connectors = {
        'hive': HiveConnector,
        'kingbase8': KingbaseConnector,
        'postgresql': KingbaseConnector,  # PostgreSQL uses same connector
        'mysql': MySQLConnector,
    }

    connector_class = connectors.get(db_type)
    if not connector_class:
        raise ValueError(f"Unsupported database type: {db_type}")

    return connector_class(connection_params)


class MySQLConnector(BaseConnector):
    """MySQL database connector"""

    def __init__(self, connection_params: Dict[str, Any]):
        super().__init__(connection_params)
        self.host = connection_params.get('host', 'localhost')
        self.port = connection_params.get('port', 3306)
        self.database = connection_params.get('database', 'test')
        self.username = connection_params.get('username', 'root')
        self.password = connection_params.get('password', '')
        self.charset = connection_params.get('charset', 'utf8mb4')

    def connect(self):
        """Connect to MySQL"""
        try:
            import mysql.connector
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.username,
                password=self.password,
                charset=self.charset
            )
            return self.connection
        except ImportError:
            logger.warning("mysql-connector-python not installed")
            raise ImportError("请安装 mysql-connector-python: pip install mysql-connector-python")
        except Exception as e:
            logger.error(f"Failed to connect to MySQL: {e}")
            raise

    def disconnect(self):
        """Disconnect from MySQL"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def test_connection(self) -> Dict[str, Any]:
        """Test MySQL connection"""
        try:
            conn = self.connect()
            if conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1')
                cursor.fetchone()  # 读取结果
                cursor.close()
                conn.close()  # 先关闭连接
                self.connection = None
                return {'success': True, 'message': 'MySQL 连接成功'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """Execute MySQL query"""
        try:
            conn = self.connect()
            if not conn:
                return []

            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)

            if cursor.description:
                results = cursor.fetchall()
            else:
                results = []

            cursor.close()
            self.disconnect()
            return results
        except Exception as e:
            logger.error(f"MySQL query execution failed: {e}")
            raise

    def get_tables(self) -> List[str]:
        """Get MySQL tables from all databases the user can access"""
        try:
            conn = self.connect()
            if not conn:
                return []
            cursor = conn.cursor()

            # 获取当前数据库的所有表
            cursor.execute("""
                SELECT TABLE_SCHEMA, TABLE_NAME
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
                AND TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_SCHEMA, TABLE_NAME
            """)

            tables = []
            for row in cursor.fetchall():
                # 返回 schema.table 格式
                tables.append(f"{row[0]}.{row[1]}")

            cursor.close()
            self.disconnect()
            return tables
        except Exception as e:
            logger.error(f"Failed to get MySQL tables: {e}")
            return []

    def get_columns(self, table_name: str) -> List[Dict]:
        """Get MySQL table columns, supports schema.table format"""
        # 解析 schema 和 table
        if '.' in table_name:
            schema, table = table_name.split('.', 1)
        else:
            schema = self.database
            table = table_name

        try:
            conn = self.connect()
            if not conn:
                return []
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                ORDER BY ORDINAL_POSITION
            """, (schema, table))

            columns = []
            for row in cursor.fetchall():
                columns.append({
                    'name': row['COLUMN_NAME'],
                    'type': row['DATA_TYPE'],
                    'nullable': row['IS_NULLABLE'] == 'YES',
                    'primary_key': row['COLUMN_KEY'] == 'PRI'
                })

            cursor.close()
            self.disconnect()
            return columns
        except Exception as e:
            logger.error(f"Failed to get MySQL columns: {e}")
            return []

    def insert_data(self, table_name: str, data: List[Dict]) -> int:
        """Insert data into MySQL table"""
        if not data:
            return 0

        conn = self.connect()
        if not conn:
            return 0

        cursor = conn.cursor()
        columns = list(data[0].keys())
        placeholders = ', '.join(['%s'] * len(columns))
        query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"

        count = 0
        for row in data:
            values = [row.get(col) for col in columns]
            cursor.execute(query, values)
            count += 1

        conn.commit()
        cursor.close()
        self.disconnect()
        return count