"""
图数据库API接口

提供RESTful API用于图数据库操作
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Body, Depends
from pydantic import BaseModel, Field

from ..neo4j_connector import Neo4jConnector, get_connector, Neo4jConnectionError
from ..models.entity_model import Entity, EntityType
from ..models.relation_model import Relation, RelationType
from ..storage.entity_storage import EntityStorage
from ..storage.relation_storage import RelationStorage
from ..storage.graph_storage import GraphStorage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graph", tags=["Graph Database"])


# ==================== Pydantic模型 ====================

class EntityCreate(BaseModel):
    """创建实体请求"""
    text: str = Field(..., description="实体文本")
    type: str = Field(..., description="实体类型")
    start_pos: Optional[int] = Field(None, description="起始位置")
    end_pos: Optional[int] = Field(None, description="结束位置")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="置信度")
    source_document: Optional[str] = Field(None, description="来源文档")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class EntityUpdate(BaseModel):
    """更新实体请求"""
    text: Optional[str] = None
    type: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = None


class EntityResponse(BaseModel):
    """实体响应"""
    id: str
    text: str
    type: str
    start_pos: Optional[int] = None
    end_pos: Optional[int] = None
    confidence: float
    source_document: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RelationCreate(BaseModel):
    """创建关系请求"""
    subject: str = Field(..., description="主体实体文本")
    relation: str = Field(..., description="关系类型")
    object: str = Field(..., description="客体实体文本")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="置信度")
    source_document: Optional[str] = Field(None, description="来源文档")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class RelationUpdate(BaseModel):
    """更新关系请求"""
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = None


class RelationResponse(BaseModel):
    """关系响应"""
    id: str
    subject: str
    subject_id: Optional[str] = None
    relation: str
    object: str
    object_id: Optional[str] = None
    confidence: float
    source_document: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class NLPResultsInput(BaseModel):
    """NLP结果输入"""
    entities: List[Dict[str, Any]] = Field(..., description="实体列表")
    relations: List[Dict[str, Any]] = Field(default_factory=list, description="关系列表")
    source_document: Optional[str] = Field(None, description="来源文档")
    deduplicate: bool = Field(True, description="是否去重")


class StoreResultResponse(BaseModel):
    """存储结果响应"""
    status: str
    entities_created: int
    entities_updated: int
    relations_created: int
    relations_updated: int
    source_document: Optional[str] = None


class GraphDataResponse(BaseModel):
    """图数据响应（用于可视化）"""
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


class StatisticsResponse(BaseModel):
    """统计信息响应"""
    entities: Dict[str, Any]
    relations: Dict[str, Any]


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    connected: bool
    neo4j_available: bool
    config: Optional[Dict[str, Any]] = None
    server_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ConnectionConfig(BaseModel):
    """连接配置"""
    uri: str = Field("bolt://localhost:7687", description="Neo4j URI")
    user: str = Field("neo4j", description="用户名")
    password: str = Field(..., description="密码")
    database: str = Field("neo4j", description="数据库名")


# ==================== 依赖注入 ====================

def get_graph_storage() -> GraphStorage:
    """获取GraphStorage实例"""
    return GraphStorage()


# ==================== API类 ====================

class GraphAPI:
    """
    图数据库API类
    
    提供程序化的API访问
    """
    
    def __init__(self, connector: Optional[Neo4jConnector] = None):
        self._connector = connector or get_connector()
        self._graph_storage = GraphStorage(self._connector)
    
    @property
    def storage(self) -> GraphStorage:
        return self._graph_storage
    
    def connect(self, uri: str, user: str, password: str, **kwargs) -> bool:
        """连接到Neo4j"""
        return self._connector.connect(uri=uri, user=user, password=password, **kwargs)
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return self._connector.health_check()


# ==================== 路由端点 ====================

# ----- 连接管理 -----

@router.post("/connect", response_model=HealthResponse, summary="连接到Neo4j数据库")
async def connect_to_neo4j(config: ConnectionConfig):
    """
    连接到Neo4j数据库
    
    - **uri**: Neo4j连接URI (默认: bolt://localhost:7687)
    - **user**: 用户名 (默认: neo4j)
    - **password**: 密码
    - **database**: 数据库名 (默认: neo4j)
    """
    try:
        connector = get_connector()
        connector.connect(
            uri=config.uri,
            user=config.user,
            password=config.password,
            database=config.database
        )
        return connector.health_check()
    except Neo4jConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/health", response_model=HealthResponse, summary="健康检查")
async def health_check():
    """检查Neo4j连接状态"""
    connector = get_connector()
    return connector.health_check()


@router.post("/disconnect", summary="断开连接")
async def disconnect():
    """断开Neo4j连接"""
    connector = get_connector()
    connector.close()
    return {"status": "disconnected"}


# ----- 实体操作 -----

@router.post("/entities", response_model=EntityResponse, summary="创建实体")
async def create_entity(entity: EntityCreate, storage: GraphStorage = Depends(get_graph_storage)):
    """创建新实体"""
    try:
        entity_obj = Entity(
            text=entity.text,
            type=EntityType.from_string(entity.type),
            start_pos=entity.start_pos,
            end_pos=entity.end_pos,
            confidence=entity.confidence,
            source_document=entity.source_document,
            metadata=entity.metadata
        )
        created = storage.entities.create(entity_obj)
        return created.to_dict()
    except Neo4jConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/entities/batch", summary="批量创建实体")
async def create_entities_batch(
    entities: List[EntityCreate],
    storage: GraphStorage = Depends(get_graph_storage)
):
    """批量创建实体"""
    try:
        entity_objs = [
            Entity(
                text=e.text,
                type=EntityType.from_string(e.type),
                start_pos=e.start_pos,
                end_pos=e.end_pos,
                confidence=e.confidence,
                source_document=e.source_document,
                metadata=e.metadata
            )
            for e in entities
        ]
        created = storage.entities.create_batch(entity_objs)
        return {"created": len(created), "entities": [e.to_dict() for e in created]}
    except Neo4jConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/entities/{entity_id}", response_model=EntityResponse, summary="获取实体")
async def get_entity(entity_id: str, storage: GraphStorage = Depends(get_graph_storage)):
    """根据ID获取实体"""
    try:
        entity = storage.entities.get_by_id(entity_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        return entity.to_dict()
    except Neo4jConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/entities", summary="获取实体列表")
async def list_entities(
    type: Optional[str] = Query(None, description="实体类型过滤"),
    text: Optional[str] = Query(None, description="文本搜索"),
    source_document: Optional[str] = Query(None, description="来源文档"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0, description="最小置信度"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    storage: GraphStorage = Depends(get_graph_storage)
):
    """获取实体列表，支持过滤和分页"""
    try:
        if text or source_document or min_confidence > 0:
            entity_type = EntityType.from_string(type) if type else None
            entities = storage.entities.search(
                text_pattern=text,
                entity_type=entity_type,
                source_document=source_document,
                min_confidence=min_confidence,
                limit=limit
            )
        elif type:
            entity_type = EntityType.from_string(type)
            entities = storage.entities.get_by_type(entity_type, limit=limit, skip=skip)
        else:
            entities = storage.entities.get_all(limit=limit, skip=skip)
        
        return {
            "entities": [e.to_dict() for e in entities],
            "count": len(entities)
        }
    except Neo4jConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.put("/entities/{entity_id}", response_model=EntityResponse, summary="更新实体")
async def update_entity(
    entity_id: str,
    updates: EntityUpdate,
    storage: GraphStorage = Depends(get_graph_storage)
):
    """更新实体"""
    try:
        update_dict = {k: v for k, v in updates.dict().items() if v is not None}
        if not update_dict:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        updated = storage.entities.update(entity_id, update_dict)
        if not updated:
            raise HTTPException(status_code=404, detail="Entity not found")
        return updated.to_dict()
    except Neo4jConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.delete("/entities/{entity_id}", summary="删除实体")
async def delete_entity(entity_id: str, storage: GraphStorage = Depends(get_graph_storage)):
    """删除实体"""
    try:
        success = storage.entities.delete(entity_id)
        if not success:
            raise HTTPException(status_code=404, detail="Entity not found")
        return {"status": "deleted", "entity_id": entity_id}
    except Neo4jConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


# ----- 关系操作 -----

@router.post("/relations", response_model=RelationResponse, summary="创建关系")
async def create_relation(
    relation: RelationCreate,
    create_entities: bool = Query(True, description="如果实体不存在是否自动创建"),
    storage: GraphStorage = Depends(get_graph_storage)
):
    """创建新关系"""
    try:
        relation_obj = Relation(
            subject=relation.subject,
            relation=RelationType.from_string(relation.relation),
            object=relation.object,
            confidence=relation.confidence,
            source_document=relation.source_document,
            metadata=relation.metadata
        )
        created = storage.relations.create(relation_obj, create_entities_if_missing=create_entities)
        return created.to_dict()
    except Neo4jConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/relations/batch", summary="批量创建关系")
async def create_relations_batch(
    relations: List[RelationCreate],
    create_entities: bool = Query(True, description="如果实体不存在是否自动创建"),
    storage: GraphStorage = Depends(get_graph_storage)
):
    """批量创建关系"""
    try:
        relation_objs = [
            Relation(
                subject=r.subject,
                relation=RelationType.from_string(r.relation),
                object=r.object,
                confidence=r.confidence,
                source_document=r.source_document,
                metadata=r.metadata
            )
            for r in relations
        ]
        created = storage.relations.create_batch(relation_objs, create_entities_if_missing=create_entities)
        return {"created": len(created), "relations": [r.to_dict() for r in created]}
    except Neo4jConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/relations/{relation_id}", response_model=RelationResponse, summary="获取关系")
async def get_relation(relation_id: str, storage: GraphStorage = Depends(get_graph_storage)):
    """根据ID获取关系"""
    try:
        relation = storage.relations.get_by_id(relation_id)
        if not relation:
            raise HTTPException(status_code=404, detail="Relation not found")
        return relation.to_dict()
    except Neo4jConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/relations", summary="获取关系列表")
async def list_relations(
    type: Optional[str] = Query(None, description="关系类型过滤"),
    subject: Optional[str] = Query(None, description="主体过滤"),
    object: Optional[str] = Query(None, description="客体过滤"),
    source_document: Optional[str] = Query(None, description="来源文档"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0, description="最小置信度"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    storage: GraphStorage = Depends(get_graph_storage)
):
    """获取关系列表，支持过滤和分页"""
    try:
        if subject or object or source_document or min_confidence > 0:
            relation_type = RelationType.from_string(type) if type else None
            relations = storage.relations.search(
                subject_pattern=subject,
                object_pattern=object,
                relation_type=relation_type,
                source_document=source_document,
                min_confidence=min_confidence,
                limit=limit
            )
        elif type:
            relation_type = RelationType.from_string(type)
            relations = storage.relations.get_by_type(relation_type, limit=limit, skip=skip)
        else:
            relations = storage.relations.get_all(limit=limit, skip=skip)
        
        return {
            "relations": [r.to_dict() for r in relations],
            "count": len(relations)
        }
    except Neo4jConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.put("/relations/{relation_id}", response_model=RelationResponse, summary="更新关系")
async def update_relation(
    relation_id: str,
    updates: RelationUpdate,
    storage: GraphStorage = Depends(get_graph_storage)
):
    """更新关系"""
    try:
        update_dict = {k: v for k, v in updates.dict().items() if v is not None}
        if not update_dict:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        updated = storage.relations.update(relation_id, update_dict)
        if not updated:
            raise HTTPException(status_code=404, detail="Relation not found")
        return updated.to_dict()
    except Neo4jConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.delete("/relations/{relation_id}", summary="删除关系")
async def delete_relation(relation_id: str, storage: GraphStorage = Depends(get_graph_storage)):
    """删除关系"""
    try:
        success = storage.relations.delete(relation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Relation not found")
        return {"status": "deleted", "relation_id": relation_id}
    except Neo4jConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


# ----- NLP集成 -----

@router.post("/store-nlp-results", response_model=StoreResultResponse, summary="存储NLP处理结果")
async def store_nlp_results(
    data: NLPResultsInput,
    storage: GraphStorage = Depends(get_graph_storage)
):
    """
    存储NLP处理结果
    
    接收NLP模块输出的实体和关系，存入图数据库
    """
    try:
        result = storage.store_nlp_results(
            entities=data.entities,
            relations=data.relations,
            source_document=data.source_document,
            deduplicate=data.deduplicate
        )
        return {
            "status": "success",
            **result
        }
    except Neo4jConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


# ----- 图查询 -----

@router.get("/neighborhood/{entity_text}", response_model=GraphDataResponse, summary="获取实体邻域")
async def get_entity_neighborhood(
    entity_text: str,
    depth: int = Query(1, ge=1, le=5, description="遍历深度"),
    limit: int = Query(50, ge=1, le=500, description="节点数量限制"),
    storage: GraphStorage = Depends(get_graph_storage)
):
    """获取指定实体的邻域图数据"""
    try:
        return storage.get_entity_neighborhood(entity_text, depth=depth, limit=limit)
    except Neo4jConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/path", summary="查找实体间路径")
async def find_path(
    start: str = Query(..., description="起始实体"),
    end: str = Query(..., description="终止实体"),
    max_depth: int = Query(5, ge=1, le=10, description="最大深度"),
    storage: GraphStorage = Depends(get_graph_storage)
):
    """查找两个实体之间的最短路径"""
    try:
        paths = storage.find_path(start, end, max_depth=max_depth)
        return {"paths": paths, "count": len(paths)}
    except Neo4jConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/data", response_model=GraphDataResponse, summary="获取图数据")
async def get_graph_data(
    limit: int = Query(100, ge=1, le=1000, description="节点数量限制"),
    entity_types: Optional[str] = Query(None, description="实体类型过滤（逗号分隔）"),
    relation_types: Optional[str] = Query(None, description="关系类型过滤（逗号分隔）"),
    storage: GraphStorage = Depends(get_graph_storage)
):
    """
    获取图数据（用于可视化）
    
    返回节点和边的数据，格式兼容常见可视化库
    """
    try:
        e_types = entity_types.split(",") if entity_types else None
        r_types = relation_types.split(",") if relation_types else None
        return storage.get_graph_data(limit=limit, entity_types=e_types, relation_types=r_types)
    except Neo4jConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


# ----- 统计和管理 -----

@router.get("/statistics", response_model=StatisticsResponse, summary="获取统计信息")
async def get_statistics(storage: GraphStorage = Depends(get_graph_storage)):
    """获取图数据库统计信息"""
    try:
        return storage.get_statistics()
    except Neo4jConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/indexes", summary="创建索引")
async def create_indexes(storage: GraphStorage = Depends(get_graph_storage)):
    """创建数据库索引以提高查询性能"""
    try:
        storage.create_indexes()
        return {"status": "indexes created"}
    except Neo4jConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/export", summary="导出数据")
async def export_data(storage: GraphStorage = Depends(get_graph_storage)):
    """导出所有图数据"""
    try:
        return storage.export_to_dict()
    except Neo4jConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/import", summary="导入数据")
async def import_data(
    data: Dict[str, Any] = Body(...),
    clear_existing: bool = Query(False, description="是否清空现有数据"),
    storage: GraphStorage = Depends(get_graph_storage)
):
    """导入图数据"""
    try:
        result = storage.import_from_dict(data, clear_existing=clear_existing)
        return {"status": "imported", **result}
    except Neo4jConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.delete("/clear", summary="清空数据")
async def clear_data(
    confirm: bool = Query(False, description="确认删除"),
    storage: GraphStorage = Depends(get_graph_storage)
):
    """清空所有图数据（需要确认）"""
    if not confirm:
        raise HTTPException(status_code=400, detail="Must set confirm=true to clear data")
    try:
        result = storage.clear_all(confirm=True)
        return {"status": "cleared", **result}
    except Neo4jConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
