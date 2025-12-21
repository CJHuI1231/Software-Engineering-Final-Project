"""
图存储操作模块

提供高级图操作功能
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..neo4j_connector import Neo4jConnector, get_connector
from ..models.entity_model import Entity, EntityType
from ..models.relation_model import Relation, RelationType
from .entity_storage import EntityStorage
from .relation_storage import RelationStorage

logger = logging.getLogger(__name__)


class GraphStorage:
    """
    图存储类
    
    提供高级图操作功能，整合实体和关系的存储操作
    """
    
    def __init__(self, connector: Optional[Neo4jConnector] = None):
        """
        初始化图存储
        
        Args:
            connector: Neo4j连接器实例
        """
        self._connector = connector or get_connector()
        self._entity_storage = EntityStorage(self._connector)
        self._relation_storage = RelationStorage(self._connector)
    
    @property
    def entities(self) -> EntityStorage:
        """获取实体存储"""
        return self._entity_storage
    
    @property
    def relations(self) -> RelationStorage:
        """获取关系存储"""
        return self._relation_storage
    
    def store_nlp_results(
        self, 
        entities: List[Dict[str, Any]], 
        relations: List[Dict[str, Any]],
        source_document: Optional[str] = None,
        deduplicate: bool = True
    ) -> Dict[str, Any]:
        """
        存储NLP处理结果
        
        Args:
            entities: NLP实体列表
            relations: NLP关系列表
            source_document: 来源文档标识
            deduplicate: 是否去重
            
        Returns:
            dict: 存储结果统计
        """
        result = {
            "entities_created": 0,
            "entities_updated": 0,
            "relations_created": 0,
            "relations_updated": 0,
            "source_document": source_document
        }
        
        # 转换并存储实体
        entity_map = {}  # text -> Entity
        for nlp_entity in entities:
            entity = Entity.from_nlp_output(nlp_entity, source_document)
            
            if deduplicate:
                stored_entity, is_created = self._entity_storage.get_or_create(entity)
                entity_map[entity.text] = stored_entity
                if is_created:
                    result["entities_created"] += 1
                else:
                    result["entities_updated"] += 1
            else:
                stored_entity = self._entity_storage.create(entity)
                entity_map[entity.text] = stored_entity
                result["entities_created"] += 1
        
        # 转换并存储关系
        for nlp_relation in relations:
            relation = Relation.from_nlp_output(nlp_relation, source_document)
            
            # 设置实体ID（如果已知）
            if relation.subject in entity_map:
                relation.subject_id = entity_map[relation.subject].id
            if relation.object in entity_map:
                relation.object_id = entity_map[relation.object].id
            
            if deduplicate:
                _, is_created = self._relation_storage.get_or_create(relation)
                if is_created:
                    result["relations_created"] += 1
                else:
                    result["relations_updated"] += 1
            else:
                self._relation_storage.create(relation)
                result["relations_created"] += 1
        
        logger.info(f"Stored NLP results: {result}")
        return result
    
    def get_entity_neighborhood(
        self, 
        entity_text: str, 
        depth: int = 1,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        获取实体的邻域图
        
        Args:
            entity_text: 实体文本
            depth: 遍历深度
            limit: 节点数量限制
            
        Returns:
            dict: 包含节点和边的图数据
        """
        query = f"""
        MATCH path = (e:Entity {{text: $entity_text}})-[*1..{depth}]-(connected)
        WITH e, connected, relationships(path) as rels
        LIMIT $limit
        RETURN collect(DISTINCT e) + collect(DISTINCT connected) as nodes,
               collect(DISTINCT rels) as relationships
        """
        
        with self._connector.get_session() as session:
            result = session.run(query, entity_text=entity_text, limit=limit)
            record = result.single()
            
            if record:
                nodes = []
                edges = []
                seen_nodes = set()
                seen_edges = set()
                
                # 处理节点
                for node_list in record["nodes"]:
                    if node_list:
                        for node in (node_list if isinstance(node_list, list) else [node_list]):
                            node_data = dict(node)
                            if node_data.get("id") not in seen_nodes:
                                seen_nodes.add(node_data.get("id"))
                                nodes.append(node_data)
                
                # 处理关系
                for rel_list in record["relationships"]:
                    if rel_list:
                        for rel in (rel_list if isinstance(rel_list, list) else [rel_list]):
                            rel_id = rel.get("id") if hasattr(rel, "get") else None
                            if rel_id and rel_id not in seen_edges:
                                seen_edges.add(rel_id)
                                edges.append(dict(rel) if hasattr(rel, "__iter__") else {})
                
                return {"nodes": nodes, "edges": edges}
        
        return {"nodes": [], "edges": []}
    
    def find_path(
        self, 
        start_entity: str, 
        end_entity: str,
        max_depth: int = 5
    ) -> List[Dict[str, Any]]:
        """
        查找两个实体之间的路径
        
        Args:
            start_entity: 起始实体文本
            end_entity: 终止实体文本
            max_depth: 最大路径深度
            
        Returns:
            list: 路径列表
        """
        query = f"""
        MATCH path = shortestPath(
            (start:Entity {{text: $start}})-[*1..{max_depth}]-(end:Entity {{text: $end}})
        )
        RETURN [node in nodes(path) | properties(node)] as nodes,
               [rel in relationships(path) | {{type: type(rel), properties: properties(rel)}}] as relationships
        """
        
        paths = []
        with self._connector.get_session() as session:
            result = session.run(query, start=start_entity, end=end_entity)
            for record in result:
                paths.append({
                    "nodes": record["nodes"],
                    "relationships": record["relationships"]
                })
        
        return paths
    
    def get_graph_data(
        self,
        limit: int = 100,
        entity_types: Optional[List[str]] = None,
        relation_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        获取图数据（用于可视化）
        
        Args:
            limit: 节点数量限制
            entity_types: 实体类型过滤
            relation_types: 关系类型过滤
            
        Returns:
            dict: 图数据（节点和边）
        """
        # 构建实体类型过滤
        entity_filter = ""
        if entity_types:
            entity_labels = ":".join(entity_types)
            entity_filter = f":{entity_labels}"
        
        # 构建关系类型过滤
        rel_filter = ""
        if relation_types:
            rel_types = "|".join([rt.upper() for rt in relation_types])
            rel_filter = f":{rel_types}"
        
        query = f"""
        MATCH (e:Entity{entity_filter})
        WITH e LIMIT $limit
        OPTIONAL MATCH (e)-[r{rel_filter}]->(e2:Entity)
        RETURN collect(DISTINCT properties(e)) as entities,
               collect(DISTINCT {{
                   source: e.id, 
                   target: e2.id, 
                   type: type(r), 
                   properties: properties(r)
               }}) as relations
        """
        
        with self._connector.get_session() as session:
            result = session.run(query, limit=limit)
            record = result.single()
            
            if record:
                # 过滤掉空关系
                relations = [r for r in record["relations"] if r.get("target")]
                return {
                    "nodes": record["entities"],
                    "edges": relations
                }
        
        return {"nodes": [], "edges": []}
    
    def clear_all(self, confirm: bool = False) -> Dict[str, int]:
        """
        清空所有数据
        
        Args:
            confirm: 确认删除
            
        Returns:
            dict: 删除统计
        """
        if not confirm:
            raise ValueError("Must set confirm=True to clear all data")
        
        # 统计现有数据
        entity_count = self._entity_storage.count()
        relation_count = self._relation_storage.count()
        
        # 删除所有数据
        query = """
        MATCH (n)
        DETACH DELETE n
        """
        
        with self._connector.get_session() as session:
            session.run(query)
        
        logger.warning(f"Cleared all data: {entity_count} entities, {relation_count} relations")
        
        return {
            "entities_deleted": entity_count,
            "relations_deleted": relation_count
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取图统计信息
        
        Returns:
            dict: 统计信息
        """
        return {
            "entities": self._entity_storage.get_statistics(),
            "relations": self._relation_storage.get_statistics()
        }
    
    def create_indexes(self):
        """
        创建索引以提高查询性能
        """
        indexes = [
            "CREATE INDEX entity_id IF NOT EXISTS FOR (e:Entity) ON (e.id)",
            "CREATE INDEX entity_text IF NOT EXISTS FOR (e:Entity) ON (e.text)",
            "CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)",
            "CREATE INDEX entity_source IF NOT EXISTS FOR (e:Entity) ON (e.source_document)",
        ]
        
        with self._connector.get_session() as session:
            for index_query in indexes:
                try:
                    session.run(index_query)
                    logger.info(f"Created index: {index_query}")
                except Exception as e:
                    logger.warning(f"Index creation failed: {e}")
    
    def export_to_dict(self) -> Dict[str, Any]:
        """
        导出所有数据为字典
        
        Returns:
            dict: 包含所有实体和关系的字典
        """
        entities = self._entity_storage.get_all(limit=10000)
        relations = self._relation_storage.get_all(limit=10000)
        
        return {
            "entities": [e.to_dict() for e in entities],
            "relations": [r.to_dict() for r in relations],
            "statistics": self.get_statistics(),
            "exported_at": datetime.now().isoformat()
        }
    
    def import_from_dict(self, data: Dict[str, Any], clear_existing: bool = False) -> Dict[str, int]:
        """
        从字典导入数据
        
        Args:
            data: 包含entities和relations的字典
            clear_existing: 是否清空现有数据
            
        Returns:
            dict: 导入统计
        """
        if clear_existing:
            self.clear_all(confirm=True)
        
        entities = data.get("entities", [])
        relations = data.get("relations", [])
        
        return self.store_nlp_results(entities, relations)
