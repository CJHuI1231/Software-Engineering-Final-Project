"""
文档数据模型
封装文档相关的数据库操作
"""

import time
from typing import Optional, List, Dict, Any
from datetime import datetime
from ..config.database import DatabaseConnection


class Document:
    """文档数据模型类"""
    
    def __init__(self):
        self.db = DatabaseConnection()
    
    def generate_doc_id(self) -> str:
        """
        生成文档ID（doc_001格式）
        
        Returns:
            文档ID
        """
        with self.db.get_connection() as connection:
            with connection.cursor() as cursor:
                # 查询当前最大的doc_id
                cursor.execute("SELECT doc_id FROM doc_document ORDER BY doc_id DESC LIMIT 1")
                result = cursor.fetchone()
                
                if result and result[0]:
                    # 提取数字部分并递增
                    current_id = result[0]
                    if current_id.startswith('doc_'):
                        try:
                            num = int(current_id[4:]) + 1
                            return f"doc_{num:03d}"
                        except ValueError:
                            pass
                
                # 如果没有找到记录或格式不对，从001开始
                return "doc_001"
    
    def create_document(self, user_id: str, title: str, file_path: str, 
                       file_size: int, author: Optional[str] = None, 
                       file_format: str = 'pdf', 
                       category: Optional[str] = None) -> Optional[str]:
        """
        创建新文档
        
        Args:
            user_id: 用户ID
            title: 文档标题
            file_path: 文件路径
            file_size: 文件大小（字节）
            author: 作者（可选）
            file_format: 文件格式
            category: 文档分类（可选）
            
        Returns:
            文档ID，如果创建失败返回None
        """
        doc_id = self.generate_doc_id()
        
        query = """
        INSERT INTO doc_document 
        (doc_id, user_id, title, author, file_path, file_size, file_format, category)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, (doc_id, user_id, title, author, 
                                         file_path, file_size, file_format, category))
                    connection.commit()
                    return doc_id
        except Exception as e:
            print(f"创建文档失败: {e}")
            return None
    
    def get_document_by_id(self, doc_id: str, include_deleted: bool = False) -> Optional[Dict[str, Any]]:
        """
        根据ID获取文档信息
        
        Args:
            doc_id: 文档ID
            include_deleted: 是否包含已删除的文档
            
        Returns:
            文档信息字典，如果不存在返回None
        """
        if include_deleted:
            query = """
            SELECT doc_id, user_id, title, author, upload_date, file_path, 
                   file_size, file_format, category, is_deleted
            FROM doc_document 
            WHERE doc_id = %s
            """
        else:
            query = """
            SELECT doc_id, user_id, title, author, upload_date, file_path, 
                   file_size, file_format, category, is_deleted
            FROM doc_document 
            WHERE doc_id = %s AND is_deleted = 0
            """
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute(query, (doc_id,))
                    result = cursor.fetchone()
                    
                    if result:
                        # 转换datetime为字符串
                        if result['upload_date']:
                            result['upload_date'] = result['upload_date'].isoformat()
                    
                    return result
        except Exception as e:
            print(f"获取文档失败: {e}")
            return None
    
    def list_user_documents(self, user_id: str, include_deleted: bool = False) -> List[Dict[str, Any]]:
        """
        获取用户的文档列表
        
        Args:
            user_id: 用户ID
            include_deleted: 是否包含已删除的文档
            
        Returns:
            文档列表
        """
        if include_deleted:
            query = """
            SELECT doc_id, title, author, upload_date, file_size, 
                   file_format, category, is_deleted
            FROM doc_document 
            WHERE user_id = %s
            ORDER BY upload_date DESC
            """
        else:
            query = """
            SELECT doc_id, title, author, upload_date, file_size, 
                   file_format, category
            FROM doc_document 
            WHERE user_id = %s AND is_deleted = 0
            ORDER BY upload_date DESC
            """
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute(query, (user_id,))
                    results = cursor.fetchall()
                    
                    # 转换datetime为字符串
                    for result in results:
                        if result['upload_date']:
                            result['upload_date'] = result['upload_date'].isoformat()
                    
                    return results
        except Exception as e:
            print(f"获取文档列表失败: {e}")
            return []
    
    def update_document(self, doc_id: str, **kwargs) -> bool:
        """
        更新文档信息
        
        Args:
            doc_id: 文档ID
            **kwargs: 要更新的字段
            
        Returns:
            是否更新成功
        """
        if not kwargs:
            return False
        
        # 构建动态UPDATE查询
        set_clauses = []
        values = []
        
        for field, value in kwargs.items():
            if field in ['title', 'author', 'file_path', 'file_size', 
                        'file_format', 'category']:
                set_clauses.append(f"{field} = %s")
                values.append(value)
        
        if not set_clauses:
            return False
        
        query = f"UPDATE doc_document SET {', '.join(set_clauses)} WHERE doc_id = %s"
        values.append(doc_id)
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, values)
                    connection.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            print(f"更新文档失败: {e}")
            return False
    
    def soft_delete_document(self, doc_id: str) -> bool:
        """
        软删除文档
        
        Args:
            doc_id: 文档ID
            
        Returns:
            是否删除成功
        """
        query = "UPDATE doc_document SET is_deleted = 1 WHERE doc_id = %s"
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, (doc_id,))
                    connection.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            print(f"删除文档失败: {e}")
            return False
    
    def restore_document(self, doc_id: str) -> bool:
        """
        恢复已删除的文档
        
        Args:
            doc_id: 文档ID
            
        Returns:
            是否恢复成功
        """
        query = "UPDATE doc_document SET is_deleted = 0 WHERE doc_id = %s"
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, (doc_id,))
                    connection.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            print(f"恢复文档失败: {e}")
            return False
    
    def hard_delete_document(self, doc_id: str) -> bool:
        """
        硬删除文档（会级联删除相关数据）
        
        Args:
            doc_id: 文档ID
            
        Returns:
            是否删除成功
        """
        query = "DELETE FROM doc_document WHERE doc_id = %s"
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, (doc_id,))
                    connection.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            print(f"硬删除文档失败: {e}")
            return False
    
    def search_documents(self, user_id: str, keyword: str, 
                        search_type: str = 'title') -> List[Dict[str, Any]]:
        """
        搜索文档
        
        Args:
            user_id: 用户ID
            keyword: 搜索关键词
            search_type: 搜索类型（title/author/category）
            
        Returns:
            搜索结果列表
        """
        if search_type == 'title':
            query = """
            SELECT doc_id, title, author, upload_date, file_size, 
                   file_format, category
            FROM doc_document 
            WHERE user_id = %s AND is_deleted = 0 AND title LIKE %s
            ORDER BY upload_date DESC
            """
            search_param = f"%{keyword}%"
        elif search_type == 'author':
            query = """
            SELECT doc_id, title, author, upload_date, file_size, 
                   file_format, category
            FROM doc_document 
            WHERE user_id = %s AND is_deleted = 0 AND author LIKE %s
            ORDER BY upload_date DESC
            """
            search_param = f"%{keyword}%"
        elif search_type == 'category':
            query = """
            SELECT doc_id, title, author, upload_date, file_size, 
                   file_format, category
            FROM doc_document 
            WHERE user_id = %s AND is_deleted = 0 AND category = %s
            ORDER BY upload_date DESC
            """
            search_param = keyword
        else:
            return []
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute(query, (user_id, search_param))
                    results = cursor.fetchall()
                    
                    # 转换datetime为字符串
                    for result in results:
                        if result['upload_date']:
                            result['upload_date'] = result['upload_date'].isoformat()
                    
                    return results
        except Exception as e:
            print(f"搜索文档失败: {e}")
            return []
    
    def get_document_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取文档统计信息
        
        Args:
            user_id: 用户ID（可选，如果不提供则统计所有用户的文档）
            
        Returns:
            统计信息字典
        """
        if user_id:
            query = """
            SELECT 
                COUNT(*) as total_docs,
                COUNT(CASE WHEN is_deleted = 0 THEN 1 END) as active_docs,
                COUNT(CASE WHEN is_deleted = 1 THEN 1 END) as deleted_docs,
                SUM(file_size) as total_size,
                AVG(file_size) as avg_size,
                COUNT(DISTINCT category) as category_count
            FROM doc_document 
            WHERE user_id = %s
            """
            params = (user_id,)
        else:
            query = """
            SELECT 
                COUNT(*) as total_docs,
                COUNT(CASE WHEN is_deleted = 0 THEN 1 END) as active_docs,
                COUNT(CASE WHEN is_deleted = 1 THEN 1 END) as deleted_docs,
                SUM(file_size) as total_size,
                AVG(file_size) as avg_size,
                COUNT(DISTINCT category) as category_count
            FROM doc_document
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
            print(f"获取文档统计失败: {e}")
            return {}
