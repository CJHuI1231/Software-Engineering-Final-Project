"""
文档标签数据模型
封装文档标签相关的数据库操作
"""

import time
from typing import Optional, List, Dict, Any
from datetime import datetime
from ..config.database import DatabaseConnection


class Tag:
    """文档标签数据模型类"""
    
    def __init__(self):
        self.db = DatabaseConnection()
    
    def generate_tag_id(self) -> str:
        """
        生成标签ID（tag_001格式）
        
        Returns:
            标签ID
        """
        with self.db.get_connection() as connection:
            with connection.cursor() as cursor:
                # 查询当前最大的tag_id
                cursor.execute("SELECT tag_id FROM doc_tag ORDER BY tag_id DESC LIMIT 1")
                result = cursor.fetchone()
                
                if result and result[0]:
                    # 提取数字部分并递增
                    current_id = result[0]
                    if current_id.startswith('tag_'):
                        try:
                            num = int(current_id[4:]) + 1
                            return f"tag_{num:03d}"
                        except ValueError:
                            pass
                
                # 如果没有找到记录或格式不对，从001开始
                return "tag_001"
    
    def create_tag(self, doc_id: str, keyword: str, 
                  synonyms: Optional[str] = None) -> Optional[str]:
        """
        创建文档标签
        
        Args:
            doc_id: 文档ID
            keyword: 标签关键词
            synonyms: 同义词（可选）
            
        Returns:
            标签ID，如果创建失败返回None
        """
        tag_id = self.generate_tag_id()
        
        query = """
        INSERT INTO doc_tag (tag_id, doc_id, keyword, synonyms)
        VALUES (%s, %s, %s, %s)
        """
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, (tag_id, doc_id, keyword, synonyms))
                    connection.commit()
                    return tag_id
        except Exception as e:
            print(f"创建标签失败: {e}")
            return None
    
    def create_multiple_tags(self, doc_id: str, keywords: List[str]) -> List[str]:
        """
        批量创建标签
        
        Args:
            doc_id: 文档ID
            keywords: 关键词列表
            
        Returns:
            成功创建的标签ID列表
        """
        tag_ids = []
        
        try:
            # 逐个创建标签，避免cursor连接问题
            for keyword in keywords:
                tag_id = self.generate_tag_id()
                query = """
                INSERT INTO doc_tag (tag_id, doc_id, keyword)
                VALUES (%s, %s, %s)
                """
                
                with self.db.get_connection() as connection:
                    with connection.cursor() as cursor:
                        cursor.execute(query, (tag_id, doc_id, keyword))
                        connection.commit()
                        tag_ids.append(tag_id)
            
            return tag_ids
        except Exception as e:
            print(f"批量创建标签失败: {e}")
            return []
    
    
    def get_tags_by_doc_id(self, doc_id: str) -> List[Dict[str, Any]]:
        """
        根据文档ID获取标签列表
        
        Args:
            doc_id: 文档ID
            
        Returns:
            标签列表
        """
        query = """
        SELECT tag_id, doc_id, keyword, synonyms, generate_time
        FROM doc_tag 
        WHERE doc_id = %s
        ORDER BY generate_time ASC
        """
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute(query, (doc_id,))
                    results = cursor.fetchall()
                    
                    # 转换datetime为字符串
                    for result in results:
                        if result['generate_time']:
                            result['generate_time'] = result['generate_time'].isoformat()
                    
                    return results
        except Exception as e:
            print(f"获取标签列表失败: {e}")
            return []
    
    def get_documents_by_keyword(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        根据关键词获取文档列表
        
        Args:
            keyword: 关键词
            limit: 返回数量限制
            
        Returns:
            文档列表
        """
        query = """
        SELECT DISTINCT t.doc_id, d.title, d.author, d.upload_date, d.user_id
        FROM doc_tag t
        JOIN doc_document d ON t.doc_id = d.doc_id
        WHERE t.keyword = %s AND d.is_deleted = 0
        ORDER BY d.upload_date DESC
        LIMIT %s
        """
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute(query, (keyword, limit))
                    results = cursor.fetchall()
                    
                    # 转换datetime为字符串
                    for result in results:
                        if result['upload_date']:
                            result['upload_date'] = result['upload_date'].isoformat()
                    
                    return results
        except Exception as e:
            print(f"获取文档列表失败: {e}")
            return []
    
    def search_documents_by_keywords(self, keywords: List[str], 
                                   match_type: str = 'any', 
                                   limit: int = 50) -> List[Dict[str, Any]]:
        """
        根据关键词列表搜索文档
        
        Args:
            keywords: 关键词列表
            match_type: 匹配类型（any/all）
            limit: 返回数量限制
            
        Returns:
            文档列表
        """
        if not keywords:
            return []
        
        if match_type == 'all':
            # 所有关键词都必须匹配
            placeholders = ', '.join(['%s'] * len(keywords))
            query = f"""
            SELECT d.doc_id, d.title, d.author, d.upload_date, d.user_id,
                   COUNT(t.tag_id) as matched_keywords
            FROM doc_document d
            JOIN doc_tag t ON d.doc_id = t.doc_id
            WHERE t.keyword IN ({placeholders}) AND d.is_deleted = 0
            GROUP BY d.doc_id, d.title, d.author, d.upload_date, d.user_id
            HAVING matched_keywords = %s
            ORDER BY d.upload_date DESC
            LIMIT %s
            """
            params = keywords + [len(keywords), limit]
        else:
            # 任意关键词匹配即可
            placeholders = ', '.join(['%s'] * len(keywords))
            query = f"""
            SELECT DISTINCT d.doc_id, d.title, d.author, d.upload_date, d.user_id
            FROM doc_document d
            JOIN doc_tag t ON d.doc_id = t.doc_id
            WHERE t.keyword IN ({placeholders}) AND d.is_deleted = 0
            ORDER BY d.upload_date DESC
            LIMIT %s
            """
            params = keywords + [limit]
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute(query, params)
                    results = cursor.fetchall()
                    
                    # 转换datetime为字符串
                    for result in results:
                        if result['upload_date']:
                            result['upload_date'] = result['upload_date'].isoformat()
                    
                    return results
        except Exception as e:
            print(f"搜索文档失败: {e}")
            return []
    
    def update_tag(self, tag_id: str, keyword: Optional[str] = None, 
                  synonyms: Optional[str] = None) -> bool:
        """
        更新标签
        
        Args:
            tag_id: 标签ID
            keyword: 新的关键词（可选）
            synonyms: 新的同义词（可选）
            
        Returns:
            是否更新成功
        """
        if not keyword and not synonyms:
            return False
        
        # 构建动态UPDATE查询
        set_clauses = []
        values = []
        
        if keyword:
            set_clauses.append("keyword = %s")
            values.append(keyword)
        
        if synonyms:
            set_clauses.append("synonyms = %s")
            values.append(synonyms)
        
        if not set_clauses:
            return False
        
        query = f"UPDATE doc_tag SET {', '.join(set_clauses)} WHERE tag_id = %s"
        values.append(tag_id)
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, values)
                    connection.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            print(f"更新标签失败: {e}")
            return False
    
    def delete_tag(self, tag_id: str) -> bool:
        """
        删除标签
        
        Args:
            tag_id: 标签ID
            
        Returns:
            是否删除成功
        """
        query = "DELETE FROM doc_tag WHERE tag_id = %s"
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, (tag_id,))
                    connection.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            print(f"删除标签失败: {e}")
            return False
    
    def delete_tags_by_doc_id(self, doc_id: str) -> bool:
        """
        删除文档的所有标签
        
        Args:
            doc_id: 文档ID
            
        Returns:
            是否删除成功
        """
        query = "DELETE FROM doc_tag WHERE doc_id = %s"
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, (doc_id,))
                    connection.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            print(f"删除文档标签失败: {e}")
            return False
    
    def get_popular_keywords(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取热门关键词
        
        Args:
            limit: 返回数量限制
            
        Returns:
            热门关键词列表
        """
        query = """
        SELECT t.keyword, COUNT(t.tag_id) as usage_count,
               COUNT(DISTINCT t.doc_id) as document_count
        FROM doc_tag t
        JOIN doc_document d ON t.doc_id = d.doc_id
        WHERE d.is_deleted = 0
        GROUP BY t.keyword
        ORDER BY usage_count DESC, document_count DESC
        LIMIT %s
        """
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute(query, (limit,))
                    return cursor.fetchall()
        except Exception as e:
            print(f"获取热门关键词失败: {e}")
            return []
    
    def get_tag_stats(self) -> Dict[str, Any]:
        """
        获取标签统计信息
        
        Returns:
            统计信息字典
        """
        query = """
        SELECT 
            COUNT(*) as total_tags,
            COUNT(DISTINCT t.keyword) as unique_keywords,
            COUNT(DISTINCT t.doc_id) as tagged_documents,
            AVG(LENGTH(t.keyword)) as avg_keyword_length,
            MAX(LENGTH(t.keyword)) as max_keyword_length
        FROM doc_tag t
        JOIN doc_document d ON t.doc_id = d.doc_id
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
            print(f"获取标签统计失败: {e}")
            return {}
