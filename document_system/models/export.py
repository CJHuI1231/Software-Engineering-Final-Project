"""
文档导出数据模型
封装文档导出相关的数据库操作
"""

import time
from typing import Optional, List, Dict, Any
from datetime import datetime
from ..config.database import DatabaseConnection


class Export:
    """文档导出数据模型类"""
    
    def __init__(self):
        self.db = DatabaseConnection()
    
    def generate_export_id(self) -> str:
        """
        生成导出ID（exp_001格式）
        
        Returns:
            导出ID
        """
        with self.db.get_connection() as connection:
            with connection.cursor() as cursor:
                # 查询当前最大的export_id
                cursor.execute("SELECT export_id FROM doc_export ORDER BY export_id DESC LIMIT 1")
                result = cursor.fetchone()
                
                if result and result[0]:
                    # 提取数字部分并递增
                    current_id = result[0]
                    if current_id.startswith('exp_'):
                        try:
                            num = int(current_id[4:]) + 1
                            return f"exp_{num:03d}"
                        except ValueError:
                            pass
                
                # 如果没有找到记录或格式不对，从001开始
                return "exp_001"
    
    def create_export(self, user_id: str, export_type: str, format: str, 
                     doc_ids: Optional[List[str]] = None,
                     export_params: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        创建导出任务
        
        Args:
            user_id: 用户ID
            export_type: 导出类型（graph/summary/document/tags）
            format: 导出格式（png/jpg/pdf/html/json）
            doc_ids: 关联文档ID列表（可选）
            export_params: 导出参数（可选）
            
        Returns:
            导出ID，如果创建失败返回None
        """
        export_id = self.generate_export_id()
        
        # 转换doc_ids为JSON字符串
        doc_ids_json = None
        if doc_ids:
            import json
            doc_ids_json = json.dumps(doc_ids)
        
        # 转换export_params为JSON字符串
        export_params_json = None
        if export_params:
            import json
            export_params_json = json.dumps(export_params)
        
        query = """
        INSERT INTO doc_export 
        (export_id, user_id, export_type, format, doc_ids, export_params)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, (export_id, user_id, export_type, format, 
                                         doc_ids_json, export_params_json))
                    connection.commit()
                    return export_id
        except Exception as e:
            print(f"创建导出任务失败: {e}")
            return None
    
    def get_export_by_id(self, export_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取导出任务信息
        
        Args:
            export_id: 导出ID
            
        Returns:
            导出任务信息字典，如果不存在返回None
        """
        query = """
        SELECT export_id, user_id, export_type, format, doc_ids, file_path,
               file_size, export_params, status, create_time, complete_time,
               error_msg, download_count
        FROM doc_export 
        WHERE export_id = %s
        """
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute(query, (export_id,))
                    result = cursor.fetchone()
                    
                    if result:
                        # 转换datetime为字符串
                        if result['create_time']:
                            result['create_time'] = result['create_time'].isoformat()
                        if result['complete_time']:
                            result['complete_time'] = result['complete_time'].isoformat()
                        
                        # 解析JSON字段
                        if result['doc_ids']:
                            import json
                            result['doc_ids'] = json.loads(result['doc_ids'])
                        if result['export_params']:
                            import json
                            result['export_params'] = json.loads(result['export_params'])
                    
                    return result
        except Exception as e:
            print(f"获取导出任务失败: {e}")
            return None
    
    def list_user_exports(self, user_id: str, status: Optional[str] = None, 
                         limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取用户的导出任务列表
        
        Args:
            user_id: 用户ID
            status: 状态过滤（可选）
            limit: 返回数量限制
            
        Returns:
            导出任务列表
        """
        if status:
            query = """
            SELECT export_id, export_type, format, status, create_time, 
                   complete_time, file_size, download_count
            FROM doc_export 
            WHERE user_id = %s AND status = %s
            ORDER BY create_time DESC
            LIMIT %s
            """
            params = (user_id, status, limit)
        else:
            query = """
            SELECT export_id, export_type, format, status, create_time, 
                   complete_time, file_size, download_count
            FROM doc_export 
            WHERE user_id = %s
            ORDER BY create_time DESC
            LIMIT %s
            """
            params = (user_id, limit)
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute(query, params)
                    results = cursor.fetchall()
                    
                    # 转换datetime为字符串
                    for result in results:
                        if result['create_time']:
                            result['create_time'] = result['create_time'].isoformat()
                        if result['complete_time']:
                            result['complete_time'] = result['complete_time'].isoformat()
                    
                    return results
        except Exception as e:
            print(f"获取导出任务列表失败: {e}")
            return []
    
    def update_export_status(self, export_id: str, status: str, 
                           file_path: Optional[str] = None,
                           file_size: Optional[int] = None,
                           error_msg: Optional[str] = None) -> bool:
        """
        更新导出任务状态
        
        Args:
            export_id: 导出ID
            status: 新状态
            file_path: 文件路径（可选）
            file_size: 文件大小（可选）
            error_msg: 错误信息（可选）
            
        Returns:
            是否更新成功
        """
        set_clauses = ["status = %s"]
        values = [status]
        
        if file_path:
            set_clauses.append("file_path = %s")
            values.append(file_path)
        
        if file_size is not None:
            set_clauses.append("file_size = %s")
            values.append(file_size)
        
        if error_msg:
            set_clauses.append("error_msg = %s")
            values.append(error_msg)
        
        # 如果状态为completed，设置完成时间
        if status == 'completed':
            set_clauses.append("complete_time = CURRENT_TIMESTAMP")
        
        query = f"UPDATE doc_export SET {', '.join(set_clauses)} WHERE export_id = %s"
        values.append(export_id)
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, values)
                    connection.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            print(f"更新导出状态失败: {e}")
            return False
    
    def increment_download_count(self, export_id: str) -> bool:
        """
        增加下载次数
        
        Args:
            export_id: 导出ID
            
        Returns:
            是否更新成功
        """
        query = """
        UPDATE doc_export 
        SET download_count = download_count + 1 
        WHERE export_id = %s
        """
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, (export_id,))
                    connection.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            print(f"增加下载次数失败: {e}")
            return False
    
    def delete_export(self, export_id: str) -> bool:
        """
        删除导出任务
        
        Args:
            export_id: 导出ID
            
        Returns:
            是否删除成功
        """
        query = "DELETE FROM doc_export WHERE export_id = %s"
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, (export_id,))
                    connection.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            print(f"删除导出任务失败: {e}")
            return False
    
    def cleanup_old_exports(self, days: int = 30) -> int:
        """
        清理旧的导出任务
        
        Args:
            days: 保留天数
            
        Returns:
            删除的任务数量
        """
        query = """
        DELETE FROM doc_export 
        WHERE create_time < DATE_SUB(NOW(), INTERVAL %s DAY)
        AND status IN ('completed', 'failed')
        """
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, (days,))
                    connection.commit()
                    return cursor.rowcount
        except Exception as e:
            print(f"清理旧导出任务失败: {e}")
            return 0
    
    def get_export_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取导出统计信息
        
        Args:
            user_id: 用户ID（可选，如果不提供则统计所有用户的导出）
            
        Returns:
            统计信息字典
        """
        if user_id:
            query = """
            SELECT 
                COUNT(*) as total_exports,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_exports,
                COUNT(CASE WHEN status = 'processing' THEN 1 END) as processing_exports,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_exports,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_exports,
                SUM(download_count) as total_downloads,
                AVG(file_size) as avg_file_size,
                SUM(file_size) as total_file_size
            FROM doc_export 
            WHERE user_id = %s
            """
            params = (user_id,)
        else:
            query = """
            SELECT 
                COUNT(*) as total_exports,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_exports,
                COUNT(CASE WHEN status = 'processing' THEN 1 END) as processing_exports,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_exports,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_exports,
                SUM(download_count) as total_downloads,
                AVG(file_size) as avg_file_size,
                SUM(file_size) as total_file_size
            FROM doc_export
            """
            params = ()
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute(query, params)
                    result = cursor.fetchone()
                    
                    # 处理NULL值
                    for key, value in result.items():
                        if value is None:
                            result[key] = 0
                    
                    return result
        except Exception as e:
            print(f"获取导出统计失败: {e}")
            return {}
    
    def get_popular_export_types(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取热门导出类型
        
        Args:
            limit: 返回数量限制
            
        Returns:
            热门导出类型列表
        """
        query = """
        SELECT 
            export_type,
            format,
            COUNT(*) as usage_count,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as success_count,
            AVG(file_size) as avg_file_size
        FROM doc_export
        GROUP BY export_type, format
        ORDER BY usage_count DESC
        LIMIT %s
        """
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute(query, (limit,))
                    results = cursor.fetchall()
                    
                    # 处理NULL值
                    for result in results:
                        if result['avg_file_size'] is None:
                            result['avg_file_size'] = 0
                    
                    return results
        except Exception as e:
            print(f"获取热门导出类型失败: {e}")
            return []
