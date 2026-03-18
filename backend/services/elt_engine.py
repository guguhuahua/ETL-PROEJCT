"""
ELT Engine Service
Handles data extraction, transformation, and loading
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)


class ELTEngine:
    """ELT Engine for data migration and transformation"""

    def execute(self, task, source_ds, target_ds) -> Dict[str, Any]:
        """
        Execute an ELT task

        Args:
            task: ELTTask model instance
            source_ds: DataSource model instance (source)
            target_ds: DataSource model instance (target)

        Returns:
            Dict with execution results
        """
        from services.db_connector import get_connector

        result = {
            'processed_rows': 0,
            'log': '',
            'start_time': datetime.utcnow().isoformat(),
            'errors': []
        }

        log_lines = []

        try:
            log_lines.append(f"[{datetime.utcnow().isoformat()}] 开始执行ELT任务: {task.name}")
            log_lines.append(f"源数据源: {source_ds.name} ({source_ds.type})")
            log_lines.append(f"目标数据源: {target_ds.name} ({target_ds.type})")

            # 获取连接器
            log_lines.append("正在连接源数据库...")
            source_connector = get_connector(source_ds.type, source_ds.get_connection_params())

            log_lines.append("正在连接目标数据库...")
            target_connector = get_connector(target_ds.type, target_ds.get_connection_params())

            # 构建源查询
            source_query = self._build_source_query(task)
            log_lines.append(f"源查询SQL: {source_query}")

            # 提取数据
            log_lines.append("正在从源数据库提取数据...")
            data = source_connector.execute_query(source_query)
            row_count = len(data)
            log_lines.append(f"提取完成，共 {row_count} 行数据")

            if row_count == 0:
                log_lines.append("源数据为空，任务结束")
                result['log'] = '\n'.join(log_lines)
                return result

            # 转换数据
            transformation_rules = task.get_transformation_rules()
            if transformation_rules and len(transformation_rules) > 0:
                log_lines.append("正在应用字段映射和转换规则...")
                data = self._transform_data(data, transformation_rules)
                log_lines.append(f"转换完成，映射了 {len(transformation_rules)} 个字段")

            # 加载数据 - 根据写入策略
            write_strategy = task.write_strategy or 'append'
            log_lines.append(f"写入策略: {'覆盖写入' if write_strategy == 'overwrite' else '追加写入'}")

            if write_strategy == 'overwrite':
                # 覆盖写入 - 先清空目标表
                log_lines.append(f"正在清空目标表: {task.target_table}...")
                try:
                    target_connector.truncate_table(task.target_table)
                    log_lines.append("目标表已清空")
                except Exception as e:
                    log_lines.append(f"清空表失败，尝试删除数据: {str(e)}")
                    target_connector.delete_all_data(task.target_table)
                    log_lines.append("目标表数据已删除")

            log_lines.append(f"正在加载数据到目标表: {task.target_table}...")
            inserted = target_connector.insert_data(task.target_table, data)
            log_lines.append(f"数据加载完成，成功插入 {inserted} 行")

            result['processed_rows'] = inserted
            result['log'] = '\n'.join(log_lines)

            log_lines.append(f"[{datetime.utcnow().isoformat()}] ELT任务执行成功")
            logger.info(f"ELT task {task.id} completed successfully, {inserted} rows processed")

            return result

        except Exception as e:
            error_msg = str(e)
            logger.error(f"ELT execution failed: {error_msg}")
            log_lines.append(f"错误: {error_msg}")
            result['errors'].append(error_msg)
            result['log'] = '\n'.join(log_lines)
            raise

    def preview_sql(self, task, source_ds, sql: Optional[str] = None) -> Dict[str, Any]:
        """
        Preview SQL query results
        """
        from services.db_connector import get_connector

        try:
            connector = get_connector(source_ds.type, source_ds.get_connection_params())

            # Use provided SQL or build from task
            query = sql if sql else self._build_source_query(task)

            # Add limit for preview
            query_upper = query.upper()
            if 'LIMIT' not in query_upper:
                query = f"{query} LIMIT 10"

            # Execute query
            data = connector.execute_query(query)

            # Get columns
            columns = []
            if data:
                for key in data[0].keys():
                    columns.append({
                        'name': key,
                        'type': type(data[0][key]).__name__,
                        'example': str(data[0][key]) if data[0][key] is not None else None
                    })

            return {
                'columns': columns,
                'preview_data': data[:10],
                'total_count': len(data)
            }

        except Exception as e:
            logger.error(f"Preview failed: {e}")
            raise

    def _build_source_query(self, task) -> str:
        """Build source query from task configuration"""
        # 根据源类型构建查询
        if task.source_type == 'sql' and task.source_sql:
            query = task.source_sql.strip()
        else:
            # 表模式 - 直接从源表查询
            source_table = task.source_table
            if not source_table:
                raise ValueError("源表名不能为空")
            query = f"SELECT * FROM {source_table}"

        # 添加时间过滤条件
        time_filter = task.get_time_filter()
        if time_filter and time_filter.get('enabled'):
            original_query = query
            query = self._apply_time_filter(query, time_filter)
            logger.info(f"Time filter applied - Field: {time_filter.get('field')}, Original: {original_query}, Filtered: {query}")
        else:
            logger.info(f"No time filter applied - Enabled: {time_filter.get('enabled') if time_filter else 'N/A'}")

        return query

    def _apply_time_filter(self, query: str, time_filter: Dict, db_type: str = None) -> str:
        """应用时间过滤条件"""
        time_field = time_filter.get('field')
        if not time_field:
            return query

        range_type = time_filter.get('range_type', 'fixed')
        conditions = []

        if range_type == 'fixed':
            # 固定时间范围
            start_time = time_filter.get('start_time')
            end_time = time_filter.get('end_time')

            if start_time:
                conditions.append(f"{time_field} >= '{start_time}'")
            if end_time:
                conditions.append(f"{time_field} <= '{end_time}'")
        else:
            # 动态时间范围
            dynamic_days = time_filter.get('dynamic_days', 7)
            dynamic_unit = time_filter.get('dynamic_unit', 'day')
            end_boundary = time_filter.get('end_boundary', 'now')

            # 计算动态时间
            now = datetime.now()
            if dynamic_unit == 'day':
                start_dt = now - timedelta(days=dynamic_days)
            elif dynamic_unit == 'hour':
                start_dt = now - timedelta(hours=dynamic_days)
            elif dynamic_unit == 'week':
                start_dt = now - timedelta(weeks=dynamic_days)
            elif dynamic_unit == 'month':
                start_dt = now - timedelta(days=dynamic_days * 30)
            else:
                start_dt = now - timedelta(days=dynamic_days)

            start_str = start_dt.strftime('%Y-%m-%d %H:%M:%S')
            conditions.append(f"{time_field} >= '{start_str}'")

            if end_boundary == 'now':
                end_str = now.strftime('%Y-%m-%d %H:%M:%S')
                conditions.append(f"{time_field} <= '{end_str}'")
            elif end_boundary == 'yesterday':
                yesterday_end = (now - timedelta(days=1)).replace(hour=23, minute=59, second=59)
                end_str = yesterday_end.strftime('%Y-%m-%d %H:%M:%S')
                conditions.append(f"{time_field} <= '{end_str}'")
            elif end_boundary == 'month_end':
                # 上月最后一天
                last_month = now.replace(day=1) - timedelta(days=1)
                month_end = last_month.replace(hour=23, minute=59, second=59)
                end_str = month_end.strftime('%Y-%m-%d %H:%M:%S')
                conditions.append(f"{time_field} <= '{end_str}'")

        if conditions:
            # 检查是否已有 WHERE 子句
            query_upper = query.upper()
            if 'WHERE' in query_upper:
                # 在现有 WHERE 后添加条件
                query = re.sub(r'WHERE', f"WHERE {' AND '.join(conditions)} AND", query, flags=re.IGNORECASE)
            else:
                # 添加新的 WHERE 子句
                # 检查是否有 GROUP BY, ORDER BY, LIMIT 等
                insert_pos = len(query)
                for keyword in ['GROUP BY', 'ORDER BY', 'LIMIT']:
                    idx = query_upper.find(keyword)
                    if idx > 0 and idx < insert_pos:
                        insert_pos = idx

                if insert_pos < len(query):
                    # 在子句前插入 WHERE
                    query = query[:insert_pos] + f" WHERE {' AND '.join(conditions)} " + query[insert_pos:]
                else:
                    query = f"{query} WHERE {' AND '.join(conditions)}"

        return query

    def _transform_data(self, data: List[Dict], rules: List[Dict]) -> List[Dict]:
        """Apply transformation rules to data"""
        if not rules:
            return data

        transformed = []

        for row in data:
            new_row = {}
            for rule in rules:
                source_field = rule.get('source_field')
                target_field = rule.get('target_field', source_field)
                transform = rule.get('transform', '')

                if not source_field:
                    continue

                value = row.get(source_field)

                # 应用转换
                if value is not None:
                    if transform == 'uppercase':
                        value = str(value).upper()
                    elif transform == 'lowercase':
                        value = str(value).lower()
                    elif transform == 'trim':
                        value = str(value).strip()
                    elif transform == 'int':
                        try:
                            value = int(float(value))
                        except (ValueError, TypeError):
                            value = 0
                    elif transform == 'float':
                        try:
                            value = float(value)
                        except (ValueError, TypeError):
                            value = 0.0
                    elif transform == 'string':
                        value = str(value)
                    elif transform == 'date_format':
                        try:
                            if isinstance(value, datetime):
                                value = value.strftime('%Y-%m-%d %H:%M:%S')
                            else:
                                value = str(value)
                        except:
                            value = str(value)
                    elif transform == 'str_to_datetime':
                        # 将标准格式时间字符串转为时间类型
                        try:
                            if isinstance(value, datetime):
                                # 已经是datetime，保持不变
                                pass
                            elif isinstance(value, str):
                                value = value.strip()
                                # 尝试多种常见的时间格式
                                formats = [
                                    '%Y-%m-%d %H:%M:%S',
                                    '%Y-%m-%d %H:%M:%S.%f',
                                    '%Y-%m-%dT%H:%M:%S',
                                    '%Y-%m-%dT%H:%M:%S.%f',
                                    '%Y-%m-%dT%H:%M:%SZ',
                                    '%Y-%m-%d',
                                    '%Y/%m/%d %H:%M:%S',
                                    '%Y/%m/%d',
                                    '%d/%m/%Y %H:%M:%S',
                                    '%d/%m/%Y',
                                ]
                                parsed = False
                                for fmt in formats:
                                    try:
                                        value = datetime.strptime(value, fmt)
                                        parsed = True
                                        break
                                    except ValueError:
                                        continue
                                if not parsed:
                                    # 如果所有格式都失败，尝试使用dateutil解析
                                    try:
                                        from dateutil import parser
                                        value = parser.parse(value)
                                    except:
                                        # 解析失败，保持原值
                                        pass
                        except Exception:
                            # 转换失败，保持原值
                            pass

                new_row[target_field] = value

            transformed.append(new_row)

        return transformed


# Singleton instance
elt_engine = ELTEngine()