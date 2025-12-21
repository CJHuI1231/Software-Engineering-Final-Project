"""
实体存储操作模块

封装实体的CRUD操作
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..neo4j_connector import Neo4jConnector, get_connector
from ..models.entity_model import Entity, EntityType, EntityCollection

logger = logging.getLogger(__name__)


class EntityStorage:
    """
    实体存储类
    
    提供实体的增删查改操作
    """
    
    def __init__(self, connector: Optional[Neo4jConnector] = None):
        """
        初始化实体存储
        
        Args:
            connector: Neo4j连接器实例，如果为None则使用单例
        """
        self._connector = connector or get_connector()
    
    def create(self, entity: Entity) -> Entity:
        """
        创建实体节点
        
        Args:
            entity: 实体对象
            
        Returns:
            Entity: 创建的实体（包含ID）
        """
        props = entity.to_neo4j_properties()
        entity_type = entity.type.value if isinstance(entity.type, EntityType) else entity.type
        
        query = f"""
        CREATE (e:Entity:{entity_type} $props)
        RETURN e
        """
        
        with self._connector.get_session() as session:
            result = session.run(query, props=props)
            record = result.single()
            if record:
                logger.info(f"Created entity: {entity.text} ({entity_type})")
                return entity
        
        return entity
    
    def create_batch(self, entities: List[Entity]) -> List[Entity]:
        """
        批量创建实体节点
        
        Args:
            entities: 实体列表
            
        Returns:
            List[Entity]: 创建的实体列表
        """
        if not entities:
            return []
        
        created = []
        
        # 按类型分组批量创建
        type_groups: Dict[str, List[Entity]] = {}
        for entity in entities:
            entity_type = entity.type.value if isinstance(entity.type, EntityType) else entity.type
            if entity_type not in type_groups:
                type_groups[entity_type] = []
            type_groups[entity_type].append(entity)
        
        with self._connector.get_session() as session:
            for entity_type, group in type_groups.items():
                props_list = [e.to_neo4j_properties() for e in group]
                
                query = f"""
                UNWIND $props_list AS props
                CREATE (e:Entity:{entity_type})
                SET e = props
                RETURN e
                """
                
                session.run(query, props_list=props_list)
                created.extend(group)
                logger.info(f"Batch created {len(group)} entities of type {entity_type}")
        
        return created
    
    def get_by_id(self, entity_id: str) -> Optional[Entity]:
        """
        根据ID获取实体
        
        Args:
            entity_id: 实体ID
            
        Returns:
            Optional[Entity]: 实体对象，不存在返回None
        """
        query = """
        MATCH (e:Entity {id: $entity_id})
        RETURN e
        """
        
        with self._connector.get_session() as session:
            result = session.run(query, entity_id=entity_id)
            record = result.single()
            if record:
                node_data = dict(record["e"])
                return Entity.from_neo4j_node(node_data)
        
        return None
    
    def get_by_text(self, text: str, entity_type: Optional[EntityType] = None) -> List[Entity]:
        """
        根据文本获取实体
        
        Args:
            text: 实体文本
            entity_type: 可选的实体类型过滤
            
        Returns:
            List[Entity]: 匹配的实体列表
        """
        if entity_type:
            type_val = entity_type.value if isinstance(entity_type, EntityType) else entity_type
            query = f"""
            MATCH (e:Entity:{type_val} {{text: $text}})
            RETURN e
            """
        else:
            query = """
            MATCH (e:Entity {text: $text})
            RETURN e
            """
        
        entities = []
        with self._connector.get_session() as session:
            result = session.run(query, text=text)
            for record in result:
                node_data = dict(record["e"])
                entities.append(Entity.from_neo4j_node(node_data))
        
        return entities
    
    def get_by_type(self, entity_type: EntityType, limit: int = 100, skip: int = 0) -> List[Entity]:
        """
        根据类型获取实体
        
        Args:
            entity_type: 实体类型
            limit: 返回数量限制
            skip: 跳过数量
            
        Returns:
            List[Entity]: 实体列表
        """
        type_val = entity_type.value if isinstance(entity_type, EntityType) else entity_type
        
        query = f"""
        MATCH (e:Entity:{type_val})
        RETURN e
        ORDER BY e.created_at DESC
        SKIP $skip
        LIMIT $limit
        """
        
        entities = []
        with self._connector.get_session() as session:
            result = session.run(query, skip=skip, limit=limit)
            for record in result:
                node_data = dict(record["e"])
                entities.append(Entity.from_neo4j_node(node_data))
        
        return entities
    
    def get_all(self, limit: int = 100, skip: int = 0) -> List[Entity]:
        """
        获取所有实体
        
        Args:
            limit: 返回数量限制
            skip: 跳过数量
            
        Returns:
            List[Entity]: 实体列表
        """
        query = """
        MATCH (e:Entity)
        RETURN e
        ORDER BY e.created_at DESC
        SKIP $skip
        LIMIT $limit
        """
        
        entities = []
        with self._connector.get_session() as session:
            result = session.run(query, skip=skip, limit=limit)
            for record in result:
                node_data = dict(record["e"])
                entities.append(Entity.from_neo4j_node(node_data))
        
        return entities
    
    def search(
        self, 
        text_pattern: Optional[str] = None,
        entity_type: Optional[EntityType] = None,
        source_document: Optional[str] = None,
        min_confidence: float = 0.0,
        limit: int = 100
    ) -> List[Entity]:
        """
        搜索实体
        
        Args:
            text_pattern: 文本模式（支持正则）
            entity_type: 实体类型
            source_document: 来源文档
            min_confidence: 最小置信度
            limit: 返回数量限制
            
        Returns:
            List[Entity]: 匹配的实体列表
        """
        conditions = ["e.confidence >= $min_confidence"]
        params = {"min_confidence": min_confidence, "limit": limit}
        
        if text_pattern:
            conditions.append("e.text =~ $text_pattern")
            params["text_pattern"] = f".*{text_pattern}.*"
        
        if source_document:
            conditions.append("e.source_document = $source_document")
            params["source_document"] = source_document
        
        type_filter = ""
        if entity_type:
            type_val = entity_type.value if isinstance(entity_type, EntityType) else entity_type
            type_filter = f":{type_val}"
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
        MATCH (e:Entity{type_filter})
        WHERE {where_clause}
        RETURN e
        ORDER BY e.confidence DESC, e.created_at DESC
        LIMIT $limit
        """
        
        entities = []
        with self._connector.get_session() as session:
            result = session.run(query, **params)
            for record in result:
                node_data = dict(record["e"])
                entities.append(Entity.from_neo4j_node(node_data))
        
        return entities
    
    def update(self, entity_id: str, updates: Dict[str, Any]) -> Optional[Entity]:
        """
        更新实体
        
        Args:
            entity_id: 实体ID
            updates: 更新的字段字典
            
        Returns:
            Optional[Entity]: 更新后的实体，不存在返回None
        """
        # 添加更新时间
        updates["updated_at"] = datetime.now().isoformat()
        
        # 构建SET子句
        set_clauses = [f"e.{key} = ${key}" for key in updates.keys()]
        set_clause = ", ".join(set_clauses)
        
        query = f"""
        MATCH (e:Entity {{id: $entity_id}})
        SET {set_clause}
        RETURN e
        """
        
        params = {"entity_id": entity_id, **updates}
        
        with self._connector.get_session() as session:
            result = session.run(query, **params)
            record = result.single()
            if record:
                node_data = dict(record["e"])
                logger.info(f"Updated entity: {entity_id}")
                return Entity.from_neo4j_node(node_data)
        
        return None
    
    def delete(self, entity_id: str) -> bool:
        """
        删除实体
        
        Args:
            entity_id: 实体ID
            
        Returns:
            bool: 是否删除成功
        """
        # 先删除关联的关系，再删除节点
        query = """
        MATCH (e:Entity {id: $entity_id})
        DETACH DELETE e
        RETURN count(e) as deleted
        """
        
        with self._connector.get_session() as session:
            result = session.run(query, entity_id=entity_id)
            record = result.single()
            if record and record["deleted"] > 0:
                logger.info(f"Deleted entity: {entity_id}")
                return True
        
        return False
    
    def delete_batch(self, entity_ids: List[str]) -> int:
        """
        批量删除实体
        
        Args:
            entity_ids: 实体ID列表
            
        Returns:
            int: 删除的数量
        """
        query = """
        MATCH (e:Entity)
        WHERE e.id IN $entity_ids
        DETACH DELETE e
        RETURN count(e) as deleted
        """
        
        with self._connector.get_session() as session:
            result = session.run(query, entity_ids=entity_ids)
            record = result.single()
            deleted = record["deleted"] if record else 0
            logger.info(f"Batch deleted {deleted} entities")
            return deleted
    
    def count(self, entity_type: Optional[EntityType] = None) -> int:
        """
        统计实体数量
        
        Args:
            entity_type: 可选的实体类型过滤
            
        Returns:
            int: 实体数量
        """
        if entity_type:
            type_val = entity_type.value if isinstance(entity_type, EntityType) else entity_type
            query = f"""
            MATCH (e:Entity:{type_val})
            RETURN count(e) as count
            """
        else:
            query = """
            MATCH (e:Entity)
            RETURN count(e) as count
            """
        
        with self._connector.get_session() as session:
            result = session.run(query)
            record = result.single()
            return record["count"] if record else 0
    
    def get_or_create(self, entity: Entity) -> tuple[Entity, bool]:
        """
        获取或创建实体（如果不存在则创建）
        
        Args:
            entity: 实体对象
            
        Returns:
            tuple: (实体对象, 是否新创建)
        """
        props = entity.to_neo4j_properties()
        entity_type = entity.type.value if isinstance(entity.type, EntityType) else entity.type
        
        query = f"""
        MERGE (e:Entity:{entity_type} {{text: $text, type: $type}})
        ON CREATE SET e = $props
        ON MATCH SET e.updated_at = $updated_at
        RETURN e, e.created_at = e.updated_at AS created
        """
        
        params = {
            "text": entity.text,
            "type": entity_type,
            "props": props,
            "updated_at": datetime.now().isoformat()
        }
        
        with self._connector.get_session() as session:
            result = session.run(query, **params)
            record = result.single()
            if record:
                node_data = dict(record["e"])
                result_entity = Entity.from_neo4j_node(node_data)
                is_created = record["created"]
                return result_entity, is_created
        
        return entity, False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取实体统计信息
        
        Returns:
            dict: 统计信息
        """
        query = """
        MATCH (e:Entity)
        RETURN e.type as type, count(e) as count
        ORDER BY count DESC
        """
        
        stats = {
            "total": 0,
            "by_type": {}
        }
        
        with self._connector.get_session() as session:
            result = session.run(query)
            for record in result:
                entity_type = record["type"]
                count = record["count"]
                stats["by_type"][entity_type] = count
                stats["total"] += count
        
        return stats
