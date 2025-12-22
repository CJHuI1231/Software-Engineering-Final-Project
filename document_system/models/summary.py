"""
文档摘要数据模型
封装文档摘要相关的数据库操作
"""

import time
from typing import Optional, List, Dict, Any
from datetime import datetime
from ..config.database import DatabaseConnection


class Summary:
    """文档摘要数据模型类"""
    
    def __init__(self):
        self.db = DatabaseConnection()
    
    def generate_summary_id(self) -> str:
        """
        生成摘要ID（sum_001格式）
        
        Returns:
            摘要ID
        """
        with self.db.get_connection() as connection:
            with connection.cursor() as cursor:
                # 查询当前最大的summary_id
                cursor.execute("SELECT summary_id FROM doc_summary ORDER BY summary_id DESC LIMIT 1")
                result = cursor.fetchone()
                
                if result and result[0]:
                    # 提取数字部分并递增
                    current_id = result[0]
                    if current_id.startswith('sum_'):
                        try:
                            num = int(current_id[4:]) + 1
                            return f"sum_{num:03d}"
                        except ValueError:
                            pass
                
                # 如果没有找到记录或格式不对，从001开始
                return "sum_001"
    
    def create_summary(self, doc_id: str, content: str, 
                      length_type: str = 'medium') -> Optional[str]:
        """
        创建文档摘要
        
        Args:
            doc_id: 文档ID
            content: 摘要内容
            length_type: 摘要长度类型（short/medium/long）
            
        Returns:
            摘要ID，如果创建失败返回None
        """
        summary_id = self.generate_summary_id()
        
        query = """
        INSERT INTO doc_summary (summary_id, doc_id, content, length_type)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
        content = VALUES(content),
        length_type = VALUES(length_type),
        generate_time = CURRENT_TIMESTAMP
        """
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, (summary_id, doc_id, content, length_type))
                    connection.commit()
                    return summary_id
        except Exception as e:
            print(f"创建摘要失败: {e}")
            return None
    
    def get_summary_by_doc_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        根据文档ID获取摘要
        
        Args:
            doc_id: 文档ID
            
        Returns:
            摘要信息字典，如果不存在返回None
        """
        query = """
        SELECT summary_id, doc_id, content, length_type, generate_time
        FROM doc_summary 
        WHERE doc_id = %s
        """
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute(query, (doc_id,))
                    result = cursor.fetchone()
                    
                    if result:
                        # 转换datetime为字符串
                        if result['generate_time']:
                            result['generate_time'] = result['generate_time'].isoformat()
                    
                    return result
        except Exception as e:
            print(f"获取摘要失败: {e}")
            return None
    
    def update_summary(self, doc_id: str, content: Optional[str] = None, 
                      length_type: Optional[str] = None) -> bool:
        """
        更新摘要
        
        Args:
            doc_id: 文档ID
            content: 新的摘要内容（可选）
            length_type: 新的长度类型（可选）
            
        Returns:
            是否更新成功
        """
        if not content and not length_type:
            return False
        
        # 构建动态UPDATE查询
        set_clauses = []
        values = []
        
        if content:
            set_clauses.append("content = %s")
            values.append(content)
        
        if length_type:
            set_clauses.append("length_type = %s")
            values.append(length_type)
        
        set_clauses.append("generate_time = CURRENT_TIMESTAMP")
        
        query = f"UPDATE doc_summary SET {', '.join(set_clauses)} WHERE doc_id = %s"
        values.append(doc_id)
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, values)
                    connection.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            print(f"更新摘要失败: {e}")
            return False
    
    def delete_summary(self, doc_id: str) -> bool:
        """
        删除摘要
        
        Args:
            doc_id: 文档ID
            
        Returns:
            是否删除成功
        """
        query = "DELETE FROM doc_summary WHERE doc_id = %s"
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, (doc_id,))
                    connection.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            print(f"删除摘要失败: {e}")
            return False
    
    def list_summaries_by_length_type(self, length_type: str, 
                                    limit: int = 100) -> List[Dict[str, Any]]:
        """
        根据长度类型列出摘要
        
        Args:
            length_type: 长度类型
            limit: 返回数量限制
            
        Returns:
            摘要列表
        """
        query = """
        SELECT s.summary_id, s.doc_id, s.content, s.length_type, s.generate_time,
               d.title, d.user_id
        FROM doc_summary s
        JOIN doc_document d ON s.doc_id = d.doc_id
        WHERE s.length_type = %s AND d.is_deleted = 0
        ORDER BY s.generate_time DESC
        LIMIT %s
        """
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute(query, (length_type, limit))
                    results = cursor.fetchall()
                    
                    # 转换datetime为字符串
                    for result in results:
                        if result['generate_time']:
                            result['generate_time'] = result['generate_time'].isoformat()
                    
                    return results
        except Exception as e:
            print(f"获取摘要列表失败: {e}")
            return []
    
    def search_summaries(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        搜索摘要内容
        
        Args:
            keyword: 搜索关键词
            limit: 返回数量限制
            
        Returns:
            搜索结果列表
        """
        query = """
        SELECT s.summary_id, s.doc_id, s.content, s.length_type, s.generate_time,
               d.title, d.user_id
        FROM doc_summary s
        JOIN doc_document d ON s.doc_id = d.doc_id
        WHERE s.content LIKE %s AND d.is_deleted = 0
        ORDER BY s.generate_time DESC
        LIMIT %s
        """
        search_param = f"%{keyword}%"
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute(query, (search_param, limit))
                    results = cursor.fetchall()
                    
                    # 转换datetime为字符串
                    for result in results:
                        if result['generate_time']:
                            result['generate_time'] = result['generate_time'].isoformat()
                    
                    return results
        except Exception as e:
            print(f"搜索摘要失败: {e}")
            return []
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """
        获取摘要统计信息
        
        Returns:
            统计信息字典
        """
        query = """
        SELECT 
            COUNT(*) as total_summaries,
            COUNT(CASE WHEN length_type = 'short' THEN 1 END) as short_summaries,
            COUNT(CASE WHEN length_type = 'medium' THEN 1 END) as medium_summaries,
            COUNT(CASE WHEN length_type = 'long' THEN 1 END) as long_summaries,
            AVG(LENGTH(content)) as avg_content_length,
            MAX(LENGTH(content)) as max_content_length,
            MIN(LENGTH(content)) as min_content_length
        FROM doc_summary s
        JOIN doc_document d ON s.doc_id = d.doc_id
        WHERE d.is_deleted = 0
        """
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute(query)
                    result = cursor.fetchone()
                    
                    # 处理NULL值
                    for key, value in result.items():
                        if value is None:
                            result[key] = 0
                    
                    return result
        except Exception as e:
            print(f"获取摘要统计失败: {e}")
            return {}
