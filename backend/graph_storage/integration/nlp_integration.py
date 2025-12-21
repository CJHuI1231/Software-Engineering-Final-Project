"""
NLP模块集成

提供与NLP模块的集成功能，支持自动和手动两种存储模式
"""

import logging
import asyncio
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime

from ..neo4j_connector import Neo4jConnector, get_connector, Neo4jConnectionError
from ..models.entity_model import Entity, EntityType, EntityCollection
from ..models.relation_model import Relation, RelationType, RelationCollection
from ..storage.graph_storage import GraphStorage

logger = logging.getLogger(__name__)


class NLPIntegration:
    """
    NLP集成服务
    
    提供将NLP处理结果存储到图数据库的功能，支持：
    - 自动存储模式：NLP处理后自动触发存储
    - 手动存储模式：手动调用存储方法
    """
    
    def __init__(
        self,
        connector: Optional[Neo4jConnector] = None,
        auto_store: bool = False,
        deduplicate: bool = True
    ):
        """
        初始化NLP集成服务
        
        Args:
            connector: Neo4j连接器实例
            auto_store: 是否启用自动存储模式
            deduplicate: 是否去重
        """
        self._connector = connector or get_connector()
        self._graph_storage = GraphStorage(self._connector)
        self._auto_store = auto_store
        self._deduplicate = deduplicate
        self._callbacks: List[Callable] = []
    
    @property
    def auto_store(self) -> bool:
        """是否启用自动存储"""
        return self._auto_store
    
    @auto_store.setter
    def auto_store(self, value: bool):
        """设置自动存储模式"""
        self._auto_store = value
    
    def register_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """
        注册存储完成回调
        
        Args:
            callback: 回调函数，接收存储结果字典
        """
        self._callbacks.append(callback)
    
    def store_entities(
        self,
        entities: List[Dict[str, Any]],
        source_document: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        存储实体到图数据库
        
        Args:
            entities: NLP实体列表，格式:
                [{"text": "张三", "type": "PERSON", "confidence": 0.95, ...}]
            source_document: 来源文档标识
            
        Returns:
            dict: 存储结果统计
        """
        result = {
            "entities_created": 0,
            "entities_updated": 0,
            "source_document": source_document,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            for nlp_entity in entities:
                entity = Entity.from_nlp_output(nlp_entity, source_document)
                
                if self._deduplicate:
                    _, is_created = self._graph_storage.entities.get_or_create(entity)
                    if is_created:
                        result["entities_created"] += 1
                    else:
                        result["entities_updated"] += 1
                else:
                    self._graph_storage.entities.create(entity)
                    result["entities_created"] += 1
            
            result["status"] = "success"
            logger.info(f"Stored {result['entities_created']} entities, updated {result['entities_updated']}")
            
        except Neo4jConnectionError as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"Failed to store entities: {e}")
        
        # 触发回调
        for callback in self._callbacks:
            try:
                callback(result)
            except Exception as e:
                logger.error(f"Callback error: {e}")
        
        return result
    
    def store_relations(
        self,
        relations: List[Dict[str, Any]],
        source_document: Optional[str] = None,
        create_entities_if_missing: bool = True
    ) -> Dict[str, Any]:
        """
        存储关系到图数据库
        
        Args:
            relations: NLP关系列表，格式:
                [{"subject": "张三", "relation": "works_at", "object": "阿里巴巴", ...}]
            source_document: 来源文档标识
            create_entities_if_missing: 如果实体不存在是否自动创建
            
        Returns:
            dict: 存储结果统计
        """
        result = {
            "relations_created": 0,
            "relations_updated": 0,
            "source_document": source_document,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            for nlp_relation in relations:
                relation = Relation.from_nlp_output(nlp_relation, source_document)
                
                if self._deduplicate:
                    _, is_created = self._graph_storage.relations.get_or_create(
                        relation, 
                        create_entities_if_missing=create_entities_if_missing
                    )
                    if is_created:
                        result["relations_created"] += 1
                    else:
                        result["relations_updated"] += 1
                else:
                    self._graph_storage.relations.create(
                        relation,
                        create_entities_if_missing=create_entities_if_missing
                    )
                    result["relations_created"] += 1
            
            result["status"] = "success"
            logger.info(f"Stored {result['relations_created']} relations, updated {result['relations_updated']}")
            
        except Neo4jConnectionError as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"Failed to store relations: {e}")
        
        # 触发回调
        for callback in self._callbacks:
            try:
                callback(result)
            except Exception as e:
                logger.error(f"Callback error: {e}")
        
        return result
    
    def store_nlp_results(
        self,
        entities: List[Dict[str, Any]],
        relations: Optional[List[Dict[str, Any]]] = None,
        source_document: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        存储完整的NLP处理结果
        
        Args:
            entities: 实体列表
            relations: 关系列表
            source_document: 来源文档标识
            
        Returns:
            dict: 存储结果统计
        """
        return self._graph_storage.store_nlp_results(
            entities=entities,
            relations=relations or [],
            source_document=source_document,
            deduplicate=self._deduplicate
        )
    
    def process_and_store(
        self,
        nlp_response: Dict[str, Any],
        source_document: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理NLP API响应并存储
        
        支持直接处理NLP模块的API响应格式
        
        Args:
            nlp_response: NLP API响应，格式:
                {
                    "status": "success",
                    "entities": [...],
                    "relations": [...],
                    ...
                }
            source_document: 来源文档标识
            
        Returns:
            dict: 存储结果统计
        """
        if nlp_response.get("status") != "success":
            return {
                "status": "skipped",
                "reason": "NLP processing was not successful",
                "nlp_status": nlp_response.get("status")
            }
        
        entities = nlp_response.get("entities", [])
        relations = nlp_response.get("relations", [])
        
        return self.store_nlp_results(
            entities=entities,
            relations=relations,
            source_document=source_document
        )
    
    async def store_nlp_results_async(
        self,
        entities: List[Dict[str, Any]],
        relations: Optional[List[Dict[str, Any]]] = None,
        source_document: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        异步存储NLP处理结果
        
        Args:
            entities: 实体列表
            relations: 关系列表
            source_document: 来源文档标识
            
        Returns:
            dict: 存储结果统计
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.store_nlp_results(entities, relations, source_document)
        )
    
    def create_auto_store_hook(self) -> Callable:
        """
        创建自动存储钩子
        
        返回一个可以集成到NLP处理流程的钩子函数
        
        Returns:
            Callable: 钩子函数
        """
        def hook(nlp_result: Dict[str, Any], source_document: Optional[str] = None):
            if self._auto_store:
                return self.process_and_store(nlp_result, source_document)
            return None
        
        return hook
    
    def get_stored_entities_for_document(self, source_document: str) -> List[Entity]:
        """
        获取指定文档的所有存储实体
        
        Args:
            source_document: 文档标识
            
        Returns:
            List[Entity]: 实体列表
        """
        return self._graph_storage.entities.search(source_document=source_document)
    
    def get_stored_relations_for_document(self, source_document: str) -> List[Relation]:
        """
        获取指定文档的所有存储关系
        
        Args:
            source_document: 文档标识
            
        Returns:
            List[Relation]: 关系列表
        """
        return self._graph_storage.relations.search(source_document=source_document)
    
    def get_knowledge_graph_for_document(self, source_document: str) -> Dict[str, Any]:
        """
        获取指定文档的知识图谱数据
        
        Args:
            source_document: 文档标识
            
        Returns:
            dict: 包含节点和边的图数据
        """
        entities = self.get_stored_entities_for_document(source_document)
        relations = self.get_stored_relations_for_document(source_document)
        
        return {
            "nodes": [e.to_dict() for e in entities],
            "edges": [r.to_dict() for r in relations],
            "source_document": source_document
        }


# 便捷函数
def store_nlp_results(
    entities: List[Dict[str, Any]],
    relations: Optional[List[Dict[str, Any]]] = None,
    source_document: Optional[str] = None,
    deduplicate: bool = True
) -> Dict[str, Any]:
    """
    便捷函数：存储NLP处理结果
    
    Args:
        entities: 实体列表
        relations: 关系列表
        source_document: 来源文档标识
        deduplicate: 是否去重
        
    Returns:
        dict: 存储结果统计
    """
    integration = NLPIntegration(deduplicate=deduplicate)
    return integration.store_nlp_results(entities, relations, source_document)


def create_nlp_integration(
    auto_store: bool = False,
    deduplicate: bool = True,
    connector: Optional[Neo4jConnector] = None
) -> NLPIntegration:
    """
    创建NLP集成服务实例
    
    Args:
        auto_store: 是否启用自动存储
        deduplicate: 是否去重
        connector: Neo4j连接器
        
    Returns:
        NLPIntegration: 集成服务实例
    """
    return NLPIntegration(
        connector=connector,
        auto_store=auto_store,
        deduplicate=deduplicate
    )
