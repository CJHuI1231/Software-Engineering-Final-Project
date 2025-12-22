"""
文档实体数据模型
封装文档实体相关的数据库操作
"""

import time
from typing import Optional, List, Dict, Any
from datetime import datetime
from ..config.database import DatabaseConnection


class Entity:
    """文档实体数据模型类"""
    
    def __init__(self):
        self.db = DatabaseConnection()
    
    def generate_entity_id(self) -> str:
        """
        生成实体ID（ent_001格式）
        
        Returns:
            实体ID
        """
        with self.db.get_connection() as connection:
            with connection.cursor() as cursor:
                # 查询当前最大的entity_id
                cursor.execute("SELECT entity_id FROM doc_entity ORDER BY entity_id DESC LIMIT 1")
                result = cursor.fetchone()
                
                if result and result[0]:
                    # 提取数字部分并递增
                    current_id = result[0]
                    if current_id.startswith('ent_'):
                        try:
                            num = int(current_id[4:]) + 1
                            return f"ent_{num:03d}"
                        except ValueError:
                            pass
                
                # 如果没有找到记录或格式不对，从001开始
                return "ent_001"
    
    def create_entity(self, doc_id: str, name: str, entity_type: str) -> Optional[str]:
        """
        创建文档实体
        
        Args:
            doc_id: 文档ID
            name: 实体名称
            entity_type: 实体类型
            
        Returns:
            实体ID，如果创建失败返回None
        """
        entity_id = self.generate_entity_id()
        
        query = """
        INSERT INTO doc_entity (entity_id, doc_id, name, type)
        VALUES (%s, %s, %s, %s)
        """
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, (entity_id, doc_id, name, entity_type))
                    connection.commit()
                    return entity_id
        except Exception as e:
            print(f"创建实体失败: {e}")
            return None
    
    def create_multiple_entities(self, doc_id: str, entities: List[Dict[str, str]]) -> List[str]:
        """
        批量创建实体
        
        Args:
            doc_id: 文档ID
            entities: 实体列表，每个实体包含name和type字段
            
        Returns:
            成功创建的实体ID列表
        """
        entity_ids = []
        
        try:
            # 逐个创建实体，避免cursor连接问题
            for entity in entities:
                entity_id = self.generate_entity_id()
                query = """
                INSERT INTO doc_entity (entity_id, doc_id, name, type)
                VALUES (%s, %s, %s, %s)
                """
                
                with self.db.get_connection() as connection:
                    with connection.cursor() as cursor:
                        cursor.execute(query, (entity_id, doc_id, entity['name'], entity['type']))
                        connection.commit()
                        entity_ids.append(entity_id)
            
            return entity_ids
        except Exception as e:
            print(f"批量创建实体失败: {e}")
            return []
    
    def get_entities_by_doc_id(self, doc_id: str) -> List[Dict[str, Any]]:
        """
        根据文档ID获取实体列表
        
        Args:
            doc_id: 文档ID
            
        Returns:
            实体列表
        """
        query = """
        SELECT entity_id, doc_id, name, type, recognize_time
        FROM doc_entity 
        WHERE doc_id = %s
        ORDER BY recognize_time ASC
        """
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute(query, (doc_id,))
                    results = cursor.fetchall()
                    
                    # 转换datetime为字符串
                    for result in results:
                        if result['recognize_time']:
                            result['recognize_time'] = result['recognize_time'].isoformat()
                    
                    return results
        except Exception as e:
            print(f"获取实体列表失败: {e}")
            return []
    
    def get_documents_by_entity_name(self, entity_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        根据实体名称获取文档列表
        
        Args:
            entity_name: 实体名称
            limit: 返回数量限制
            
        Returns:
            文档列表
        """
        query = """
        SELECT DISTINCT e.doc_id, d.title, d.author, d.upload_date, d.user_id
        FROM doc_entity e
        JOIN doc_document d ON e.doc_id = d.doc_id
        WHERE e.name = %s AND d.is_deleted = 0
        ORDER BY d.upload_date DESC
        LIMIT %s
        """
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute(query, (entity_name, limit))
                    results = cursor.fetchall()
                    
                    # 转换datetime为字符串
                    for result in results:
                        if result['upload_date']:
                            result['upload_date'] = result['upload_date'].isoformat()
                    
                    return results
        except Exception as e:
            print(f"获取文档列表失败: {e}")
            return []
    
    def get_documents_by_entity_type(self, entity_type: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        根据实体类型获取文档列表
        
        Args:
            entity_type: 实体类型
            limit: 返回数量限制
            
        Returns:
            文档列表
        """
        query = """
        SELECT DISTINCT e.doc_id, d.title, d.author, d.upload_date, d.user_id
        FROM doc_entity e
        JOIN doc_document d ON e.doc_id = d.doc_id
        WHERE e.type = %s AND d.is_deleted = 0
        ORDER BY d.upload_date DESC
        LIMIT %s
        """
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute(query, (entity_type, limit))
                    results = cursor.fetchall()
                    
                    # 转换datetime为字符串
                    for result in results:
                        if result['upload_date']:
                            result['upload_date'] = result['upload_date'].isoformat()
                    
                    return results
        except Exception as e:
            print(f"获取文档列表失败: {e}")
            return []
    
    def search_documents_by_entities(self, entity_names: List[str], 
                                    match_type: str = 'any', 
                                    limit: int = 50) -> List[Dict[str, Any]]:
        """
        根据实体名称列表搜索文档
        
        Args:
            entity_names: 实体名称列表
            match_type: 匹配类型（any/all）
            limit: 返回数量限制
            
        Returns:
            文档列表
        """
        if not entity_names:
            return []
        
        if match_type == 'all':
            # 所有实体都必须匹配
            placeholders = ', '.join(['%s'] * len(entity_names))
            query = f"""
            SELECT d.doc_id, d.title, d.author, d.upload_date, d.user_id,
                   COUNT(e.entity_id) as matched_entities
            FROM doc_document d
            JOIN doc_entity e ON d.doc_id = e.doc_id
            WHERE e.name IN ({placeholders}) AND d.is_deleted = 0
            GROUP BY d.doc_id, d.title, d.author, d.upload_date, d.user_id
            HAVING matched_entities = %s
            ORDER BY d.upload_date DESC
            LIMIT %s
            """
            params = entity_names + [len(entity_names), limit]
        else:
            # 任意实体匹配即可
            placeholders = ', '.join(['%s'] * len(entity_names))
            query = f"""
            SELECT DISTINCT d.doc_id, d.title, d.author, d.upload_date, d.user_id
            FROM doc_document d
            JOIN doc_entity e ON d.doc_id = e.doc_id
            WHERE e.name IN ({placeholders}) AND d.is_deleted = 0
            ORDER BY d.upload_date DESC
            LIMIT %s
            """
            params = entity_names + [limit]
        
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
    
    def update_entity(self, entity_id: str, name: Optional[str] = None, 
                     entity_type: Optional[str] = None) -> bool:
        """
        更新实体
        
        Args:
            entity_id: 实体ID
            name: 新的实体名称（可选）
            entity_type: 新的实体类型（可选）
            
        Returns:
            是否更新成功
        """
        if not name and not entity_type:
            return False
        
        # 构建动态UPDATE查询
        set_clauses = []
        values = []
        
        if name:
            set_clauses.append("name = %s")
            values.append(name)
        
        if entity_type:
            set_clauses.append("type = %s")
            values.append(entity_type)
        
        if not set_clauses:
            return False
        
        query = f"UPDATE doc_entity SET {', '.join(set_clauses)} WHERE entity_id = %s"
        values.append(entity_id)
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, values)
                    connection.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            print(f"更新实体失败: {e}")
            return False
    
    def delete_entity(self, entity_id: str) -> bool:
        """
        删除实体
        
        Args:
            entity_id: 实体ID
            
        Returns:
            是否删除成功
        """
        query = "DELETE FROM doc_entity WHERE entity_id = %s"
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, (entity_id,))
                    connection.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            print(f"删除实体失败: {e}")
            return False
    
    def delete_entities_by_doc_id(self, doc_id: str) -> bool:
        """
        删除文档的所有实体
        
        Args:
            doc_id: 文档ID
            
        Returns:
            是否删除成功
        """
        query = "DELETE FROM doc_entity WHERE doc_id = %s"
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, (doc_id,))
                    connection.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            print(f"删除文档实体失败: {e}")
            return False
    
    def get_popular_entities(self, entity_type: Optional[str] = None, 
                           limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取热门实体
        
        Args:
            entity_type: 实体类型过滤（可选）
            limit: 返回数量限制
            
        Returns:
            热门实体列表
        """
        if entity_type:
            query = """
            SELECT e.name, e.type, COUNT(e.entity_id) as usage_count,
                   COUNT(DISTINCT e.doc_id) as document_count
            FROM doc_entity e
            JOIN doc_document d ON e.doc_id = d.doc_id
            WHERE e.type = %s AND d.is_deleted = 0
            GROUP BY e.name, e.type
            ORDER BY usage_count DESC, document_count DESC
            LIMIT %s
            """
            params = (entity_type, limit)
        else:
            query = """
            SELECT e.name, e.type, COUNT(e.entity_id) as usage_count,
                   COUNT(DISTINCT e.doc_id) as document_count
            FROM doc_entity e
            JOIN doc_document d ON e.doc_id = d.doc_id
            WHERE d.is_deleted = 0
            GROUP BY e.name, e.type
            ORDER BY usage_count DESC, document_count DESC
            LIMIT %s
            """
            params = (limit,)
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute(query, params)
                    return cursor.fetchall()
        except Exception as e:
            print(f"获取热门实体失败: {e}")
            return []
    
    def get_entity_types(self) -> List[str]:
        """
        获取所有实体类型
        
        Returns:
            实体类型列表
        """
        query = """
        SELECT DISTINCT type
        FROM doc_entity e
        JOIN doc_document d ON e.doc_id = d.doc_id
        WHERE d.is_deleted = 0
        ORDER BY type
        """
        
        try:
            with self.db.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query)
                    results = cursor.fetchall()
                    return [result[0] for result in results]
        except Exception as e:
            print(f"获取实体类型失败: {e}")
            return []
    
    def get_entity_stats(self) -> Dict[str, Any]:
        """
        获取实体统计信息
        
        Returns:
            统计信息字典
        """
        query = """
        SELECT 
            COUNT(*) as total_entities,
            COUNT(DISTINCT e.name) as unique_entities,
            COUNT(DISTINCT e.type) as entity_types,
            COUNT(DISTINCT e.doc_id) as entity_documents,
            AVG(LENGTH(e.name)) as avg_name_length,
            MAX(LENGTH(e.name)) as max_name_length
        FROM doc_entity e
        JOIN doc_document d ON e.doc_id = d.doc_id
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
            print(f"获取实体统计失败: {e}")
            return {}
