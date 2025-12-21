"""
关系存储操作模块

封装关系的CRUD操作
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..neo4j_connector import Neo4jConnector, get_connector
from ..models.relation_model import Relation, RelationType, RelationCollection
from ..models.entity_model import Entity, EntityType

logger = logging.getLogger(__name__)


class RelationStorage:
    """
    关系存储类
    
    提供关系的增删查改操作
    """
    
    def __init__(self, connector: Optional[Neo4jConnector] = None):
        """
        初始化关系存储
        
        Args:
            connector: Neo4j连接器实例，如果为None则使用单例
        """
        self._connector = connector or get_connector()
    
    def create(self, relation: Relation, create_entities_if_missing: bool = True) -> Relation:
        """
        创建关系
        
        Args:
            relation: 关系对象
            create_entities_if_missing: 如果实体不存在是否自动创建
            
        Returns:
            Relation: 创建的关系
        """
        props = relation.to_neo4j_properties()
        rel_type = relation.get_neo4j_relationship_type()
        
        if create_entities_if_missing:
            # 使用MERGE确保实体存在
            query = f"""
            MERGE (s:Entity {{text: $subject}})
            ON CREATE SET s.id = randomUUID(), s.type = 'UNKNOWN', s.confidence = 1.0, 
                          s.created_at = datetime(), s.updated_at = datetime()
            MERGE (o:Entity {{text: $object}})
            ON CREATE SET o.id = randomUUID(), o.type = 'UNKNOWN', o.confidence = 1.0,
                          o.created_at = datetime(), o.updated_at = datetime()
            CREATE (s)-[r:{rel_type} $props]->(o)
            RETURN s.id as subject_id, o.id as object_id, r
            """
        else:
            query = f"""
            MATCH (s:Entity {{text: $subject}})
            MATCH (o:Entity {{text: $object}})
            CREATE (s)-[r:{rel_type} $props]->(o)
            RETURN s.id as subject_id, o.id as object_id, r
            """
        
        params = {
            "subject": relation.subject,
            "object": relation.object,
            "props": props
        }
        
        with self._connector.get_session() as session:
            result = session.run(query, **params)
            record = result.single()
            if record:
                relation.subject_id = record["subject_id"]
                relation.object_id = record["object_id"]
                logger.info(f"Created relation: {relation}")
        
        return relation
    
    def create_batch(self, relations: List[Relation], create_entities_if_missing: bool = True) -> List[Relation]:
        """
        批量创建关系
        
        Args:
            relations: 关系列表
            create_entities_if_missing: 如果实体不存在是否自动创建
            
        Returns:
            List[Relation]: 创建的关系列表
        """
        if not relations:
            return []
        
        created = []
        
        # 按关系类型分组
        type_groups: Dict[str, List[Relation]] = {}
        for relation in relations:
            rel_type = relation.get_neo4j_relationship_type()
            if rel_type not in type_groups:
                type_groups[rel_type] = []
            type_groups[rel_type].append(relation)
        
        with self._connector.get_session() as session:
            for rel_type, group in type_groups.items():
                rel_data = []
                for r in group:
                    rel_data.append({
                        "subject": r.subject,
                        "object": r.object,
                        "props": r.to_neo4j_properties()
                    })
                
                if create_entities_if_missing:
                    query = f"""
                    UNWIND $rel_data AS data
                    MERGE (s:Entity {{text: data.subject}})
                    ON CREATE SET s.id = randomUUID(), s.type = 'UNKNOWN', s.confidence = 1.0,
                                  s.created_at = datetime(), s.updated_at = datetime()
                    MERGE (o:Entity {{text: data.object}})
                    ON CREATE SET o.id = randomUUID(), o.type = 'UNKNOWN', o.confidence = 1.0,
                                  o.created_at = datetime(), o.updated_at = datetime()
                    CREATE (s)-[r:{rel_type}]->(o)
                    SET r = data.props
                    RETURN r
                    """
                else:
                    query = f"""
                    UNWIND $rel_data AS data
                    MATCH (s:Entity {{text: data.subject}})
                    MATCH (o:Entity {{text: data.object}})
                    CREATE (s)-[r:{rel_type}]->(o)
                    SET r = data.props
                    RETURN r
                    """
                
                session.run(query, rel_data=rel_data)
                created.extend(group)
                logger.info(f"Batch created {len(group)} relations of type {rel_type}")
        
        return created
    
    def get_by_id(self, relation_id: str) -> Optional[Relation]:
        """
        根据ID获取关系
        
        Args:
            relation_id: 关系ID
            
        Returns:
            Optional[Relation]: 关系对象，不存在返回None
        """
        query = """
        MATCH (s:Entity)-[r {id: $relation_id}]->(o:Entity)
        RETURN s.text as subject, s.id as subject_id, 
               type(r) as relation_type, properties(r) as props,
               o.text as object, o.id as object_id
        """
        
        with self._connector.get_session() as session:
            result = session.run(query, relation_id=relation_id)
            record = result.single()
            if record:
                rel_data = record["props"]
                rel_data["subject"] = record["subject"]
                rel_data["subject_id"] = record["subject_id"]
                rel_data["object"] = record["object"]
                rel_data["object_id"] = record["object_id"]
                rel_data["relation"] = record["relation_type"].lower()
                return Relation.from_neo4j_relationship(rel_data)
        
        return None
    
    def get_by_entities(self, subject: str, obj: str) -> List[Relation]:
        """
        根据主体和客体获取关系
        
        Args:
            subject: 主体文本
            obj: 客体文本
            
        Returns:
            List[Relation]: 关系列表
        """
        query = """
        MATCH (s:Entity {text: $subject})-[r]->(o:Entity {text: $object})
        RETURN s.text as subject, s.id as subject_id,
               type(r) as relation_type, properties(r) as props,
               o.text as object, o.id as object_id
        """
        
        relations = []
        with self._connector.get_session() as session:
            result = session.run(query, subject=subject, object=obj)
            for record in result:
                rel_data = record["props"]
                rel_data["subject"] = record["subject"]
                rel_data["subject_id"] = record["subject_id"]
                rel_data["object"] = record["object"]
                rel_data["object_id"] = record["object_id"]
                rel_data["relation"] = record["relation_type"].lower()
                relations.append(Relation.from_neo4j_relationship(rel_data))
        
        return relations
    
    def get_by_subject(self, subject: str, relation_type: Optional[RelationType] = None) -> List[Relation]:
        """
        获取指定主体的所有关系
        
        Args:
            subject: 主体文本
            relation_type: 可选的关系类型过滤
            
        Returns:
            List[Relation]: 关系列表
        """
        if relation_type:
            rel_type = relation_type.value.upper() if isinstance(relation_type, RelationType) else relation_type.upper()
            query = f"""
            MATCH (s:Entity {{text: $subject}})-[r:{rel_type}]->(o:Entity)
            RETURN s.text as subject, s.id as subject_id,
                   type(r) as relation_type, properties(r) as props,
                   o.text as object, o.id as object_id
            """
        else:
            query = """
            MATCH (s:Entity {text: $subject})-[r]->(o:Entity)
            RETURN s.text as subject, s.id as subject_id,
                   type(r) as relation_type, properties(r) as props,
                   o.text as object, o.id as object_id
            """
        
        relations = []
        with self._connector.get_session() as session:
            result = session.run(query, subject=subject)
            for record in result:
                rel_data = record["props"]
                rel_data["subject"] = record["subject"]
                rel_data["subject_id"] = record["subject_id"]
                rel_data["object"] = record["object"]
                rel_data["object_id"] = record["object_id"]
                rel_data["relation"] = record["relation_type"].lower()
                relations.append(Relation.from_neo4j_relationship(rel_data))
        
        return relations
    
    def get_by_object(self, obj: str, relation_type: Optional[RelationType] = None) -> List[Relation]:
        """
        获取指定客体的所有关系
        
        Args:
            obj: 客体文本
            relation_type: 可选的关系类型过滤
            
        Returns:
            List[Relation]: 关系列表
        """
        if relation_type:
            rel_type = relation_type.value.upper() if isinstance(relation_type, RelationType) else relation_type.upper()
            query = f"""
            MATCH (s:Entity)-[r:{rel_type}]->(o:Entity {{text: $object}})
            RETURN s.text as subject, s.id as subject_id,
                   type(r) as relation_type, properties(r) as props,
                   o.text as object, o.id as object_id
            """
        else:
            query = """
            MATCH (s:Entity)-[r]->(o:Entity {text: $object})
            RETURN s.text as subject, s.id as subject_id,
                   type(r) as relation_type, properties(r) as props,
                   o.text as object, o.id as object_id
            """
        
        relations = []
        with self._connector.get_session() as session:
            result = session.run(query, object=obj)
            for record in result:
                rel_data = record["props"]
                rel_data["subject"] = record["subject"]
                rel_data["subject_id"] = record["subject_id"]
                rel_data["object"] = record["object"]
                rel_data["object_id"] = record["object_id"]
                rel_data["relation"] = record["relation_type"].lower()
                relations.append(Relation.from_neo4j_relationship(rel_data))
        
        return relations
    
    def get_by_type(self, relation_type: RelationType, limit: int = 100, skip: int = 0) -> List[Relation]:
        """
        根据关系类型获取关系
        
        Args:
            relation_type: 关系类型
            limit: 返回数量限制
            skip: 跳过数量
            
        Returns:
            List[Relation]: 关系列表
        """
        rel_type = relation_type.value.upper() if isinstance(relation_type, RelationType) else relation_type.upper()
        
        query = f"""
        MATCH (s:Entity)-[r:{rel_type}]->(o:Entity)
        RETURN s.text as subject, s.id as subject_id,
               type(r) as relation_type, properties(r) as props,
               o.text as object, o.id as object_id
        ORDER BY r.created_at DESC
        SKIP $skip
        LIMIT $limit
        """
        
        relations = []
        with self._connector.get_session() as session:
            result = session.run(query, skip=skip, limit=limit)
            for record in result:
                rel_data = record["props"]
                rel_data["subject"] = record["subject"]
                rel_data["subject_id"] = record["subject_id"]
                rel_data["object"] = record["object"]
                rel_data["object_id"] = record["object_id"]
                rel_data["relation"] = record["relation_type"].lower()
                relations.append(Relation.from_neo4j_relationship(rel_data))
        
        return relations
    
    def get_all(self, limit: int = 100, skip: int = 0) -> List[Relation]:
        """
        获取所有关系
        
        Args:
            limit: 返回数量限制
            skip: 跳过数量
            
        Returns:
            List[Relation]: 关系列表
        """
        query = """
        MATCH (s:Entity)-[r]->(o:Entity)
        RETURN s.text as subject, s.id as subject_id,
               type(r) as relation_type, properties(r) as props,
               o.text as object, o.id as object_id
        ORDER BY r.created_at DESC
        SKIP $skip
        LIMIT $limit
        """
        
        relations = []
        with self._connector.get_session() as session:
            result = session.run(query, skip=skip, limit=limit)
            for record in result:
                rel_data = record["props"]
                rel_data["subject"] = record["subject"]
                rel_data["subject_id"] = record["subject_id"]
                rel_data["object"] = record["object"]
                rel_data["object_id"] = record["object_id"]
                rel_data["relation"] = record["relation_type"].lower()
                relations.append(Relation.from_neo4j_relationship(rel_data))
        
        return relations
    
    def search(
        self,
        subject_pattern: Optional[str] = None,
        object_pattern: Optional[str] = None,
        relation_type: Optional[RelationType] = None,
        source_document: Optional[str] = None,
        min_confidence: float = 0.0,
        limit: int = 100
    ) -> List[Relation]:
        """
        搜索关系
        
        Args:
            subject_pattern: 主体文本模式
            object_pattern: 客体文本模式
            relation_type: 关系类型
            source_document: 来源文档
            min_confidence: 最小置信度
            limit: 返回数量限制
            
        Returns:
            List[Relation]: 匹配的关系列表
        """
        conditions = ["r.confidence >= $min_confidence"]
        params = {"min_confidence": min_confidence, "limit": limit}
        
        if subject_pattern:
            conditions.append("s.text =~ $subject_pattern")
            params["subject_pattern"] = f".*{subject_pattern}.*"
        
        if object_pattern:
            conditions.append("o.text =~ $object_pattern")
            params["object_pattern"] = f".*{object_pattern}.*"
        
        if source_document:
            conditions.append("r.source_document = $source_document")
            params["source_document"] = source_document
        
        rel_filter = ""
        if relation_type:
            rel_type = relation_type.value.upper() if isinstance(relation_type, RelationType) else relation_type.upper()
            rel_filter = f":{rel_type}"
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
        MATCH (s:Entity)-[r{rel_filter}]->(o:Entity)
        WHERE {where_clause}
        RETURN s.text as subject, s.id as subject_id,
               type(r) as relation_type, properties(r) as props,
               o.text as object, o.id as object_id
        ORDER BY r.confidence DESC, r.created_at DESC
        LIMIT $limit
        """
        
        relations = []
        with self._connector.get_session() as session:
            result = session.run(query, **params)
            for record in result:
                rel_data = record["props"]
                rel_data["subject"] = record["subject"]
                rel_data["subject_id"] = record["subject_id"]
                rel_data["object"] = record["object"]
                rel_data["object_id"] = record["object_id"]
                rel_data["relation"] = record["relation_type"].lower()
                relations.append(Relation.from_neo4j_relationship(rel_data))
        
        return relations
    
    def update(self, relation_id: str, updates: Dict[str, Any]) -> Optional[Relation]:
        """
        更新关系
        
        Args:
            relation_id: 关系ID
            updates: 更新的字段字典
            
        Returns:
            Optional[Relation]: 更新后的关系，不存在返回None
        """
        updates["updated_at"] = datetime.now().isoformat()
        
        set_clauses = [f"r.{key} = ${key}" for key in updates.keys()]
        set_clause = ", ".join(set_clauses)
        
        query = f"""
        MATCH (s:Entity)-[r {{id: $relation_id}}]->(o:Entity)
        SET {set_clause}
        RETURN s.text as subject, s.id as subject_id,
               type(r) as relation_type, properties(r) as props,
               o.text as object, o.id as object_id
        """
        
        params = {"relation_id": relation_id, **updates}
        
        with self._connector.get_session() as session:
            result = session.run(query, **params)
            record = result.single()
            if record:
                rel_data = record["props"]
                rel_data["subject"] = record["subject"]
                rel_data["subject_id"] = record["subject_id"]
                rel_data["object"] = record["object"]
                rel_data["object_id"] = record["object_id"]
                rel_data["relation"] = record["relation_type"].lower()
                logger.info(f"Updated relation: {relation_id}")
                return Relation.from_neo4j_relationship(rel_data)
        
        return None
    
    def delete(self, relation_id: str) -> bool:
        """
        删除关系
        
        Args:
            relation_id: 关系ID
            
        Returns:
            bool: 是否删除成功
        """
        query = """
        MATCH ()-[r {id: $relation_id}]->()
        DELETE r
        RETURN count(r) as deleted
        """
        
        with self._connector.get_session() as session:
            result = session.run(query, relation_id=relation_id)
            record = result.single()
            if record and record["deleted"] > 0:
                logger.info(f"Deleted relation: {relation_id}")
                return True
        
        return False
    
    def delete_batch(self, relation_ids: List[str]) -> int:
        """
        批量删除关系
        
        Args:
            relation_ids: 关系ID列表
            
        Returns:
            int: 删除的数量
        """
        query = """
        MATCH ()-[r]->()
        WHERE r.id IN $relation_ids
        DELETE r
        RETURN count(r) as deleted
        """
        
        with self._connector.get_session() as session:
            result = session.run(query, relation_ids=relation_ids)
            record = result.single()
            deleted = record["deleted"] if record else 0
            logger.info(f"Batch deleted {deleted} relations")
            return deleted
    
    def count(self, relation_type: Optional[RelationType] = None) -> int:
        """
        统计关系数量
        
        Args:
            relation_type: 可选的关系类型过滤
            
        Returns:
            int: 关系数量
        """
        if relation_type:
            rel_type = relation_type.value.upper() if isinstance(relation_type, RelationType) else relation_type.upper()
            query = f"""
            MATCH ()-[r:{rel_type}]->()
            RETURN count(r) as count
            """
        else:
            query = """
            MATCH ()-[r]->()
            RETURN count(r) as count
            """
        
        with self._connector.get_session() as session:
            result = session.run(query)
            record = result.single()
            return record["count"] if record else 0
    
    def get_or_create(self, relation: Relation, create_entities_if_missing: bool = True) -> tuple[Relation, bool]:
        """
        获取或创建关系
        
        Args:
            relation: 关系对象
            create_entities_if_missing: 如果实体不存在是否自动创建
            
        Returns:
            tuple: (关系对象, 是否新创建)
        """
        props = relation.to_neo4j_properties()
        rel_type = relation.get_neo4j_relationship_type()
        
        if create_entities_if_missing:
            query = f"""
            MERGE (s:Entity {{text: $subject}})
            ON CREATE SET s.id = randomUUID(), s.type = 'UNKNOWN', s.confidence = 1.0,
                          s.created_at = datetime(), s.updated_at = datetime()
            MERGE (o:Entity {{text: $object}})
            ON CREATE SET o.id = randomUUID(), o.type = 'UNKNOWN', o.confidence = 1.0,
                          o.created_at = datetime(), o.updated_at = datetime()
            MERGE (s)-[r:{rel_type} {{subject: $subject, object: $object}}]->(o)
            ON CREATE SET r = $props
            ON MATCH SET r.updated_at = $updated_at
            RETURN s.id as subject_id, o.id as object_id, r, r.created_at = r.updated_at AS created
            """
        else:
            query = f"""
            MATCH (s:Entity {{text: $subject}})
            MATCH (o:Entity {{text: $object}})
            MERGE (s)-[r:{rel_type} {{subject: $subject, object: $object}}]->(o)
            ON CREATE SET r = $props
            ON MATCH SET r.updated_at = $updated_at
            RETURN s.id as subject_id, o.id as object_id, r, r.created_at = r.updated_at AS created
            """
        
        params = {
            "subject": relation.subject,
            "object": relation.object,
            "props": props,
            "updated_at": datetime.now().isoformat()
        }
        
        with self._connector.get_session() as session:
            result = session.run(query, **params)
            record = result.single()
            if record:
                relation.subject_id = record["subject_id"]
                relation.object_id = record["object_id"]
                is_created = record["created"]
                return relation, is_created
        
        return relation, False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取关系统计信息
        
        Returns:
            dict: 统计信息
        """
        query = """
        MATCH ()-[r]->()
        RETURN type(r) as type, count(r) as count
        ORDER BY count DESC
        """
        
        stats = {
            "total": 0,
            "by_type": {}
        }
        
        with self._connector.get_session() as session:
            result = session.run(query)
            for record in result:
                rel_type = record["type"]
                count = record["count"]
                stats["by_type"][rel_type] = count
                stats["total"] += count
        
        return stats
