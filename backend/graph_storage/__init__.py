"""
Graph Storage 模块

Neo4j图数据库集成，用于存储通过NLP检索到的命名实体与其关系。

模块结构:
    - neo4j_connector: Neo4j连接管理
    - models: 数据模型（Entity, Relation）
    - storage: 存储操作（CRUD）
    - api: FastAPI路由
    - utils: 工具函数（配置、错误处理）
    - integration: 与其他模块的集成

使用示例:
    # 方式1: 使用便捷函数
    from backend.graph_storage import connect_neo4j, store_nlp_results
    
    # 连接数据库
    connector = connect_neo4j(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="password"
    )
    
    # 存储NLP结果
    result = store_nlp_results(
        entities=[{"text": "张三", "type": "PERSON", "confidence": 0.95}],
        relations=[{"subject": "张三", "relation": "works_at", "object": "阿里巴巴"}]
    )
    
    # 方式2: 使用API
    from fastapi import FastAPI
    from backend.graph_storage.api import router
    
    app = FastAPI()
    app.include_router(router)
    
    # 方式3: 使用GraphStorage类
    from backend.graph_storage.storage import GraphStorage
    
    storage = GraphStorage()
    entities = storage.entities.get_all()
"""

# 版本信息
__version__ = "1.0.0"
__author__ = "Your Name"

# 核心组件导入
from .neo4j_connector import (
    Neo4jConnector,
    Neo4jConnectionError,
    get_connector,
    connect_neo4j
)

# 数据模型导入
from .models import (
    Entity,
    EntityType,
    Relation,
    RelationType
)

# 存储操作导入
from .storage import (
    EntityStorage,
    RelationStorage,
    GraphStorage
)

# API导入
from .api import router, GraphAPI

# 工具导入
from .utils import (
    GraphConfig,
    load_config,
    get_default_config,
    GraphStorageError,
    ConnectionError,
    EntityNotFoundError,
    RelationNotFoundError,
    ValidationError
)

# 集成导入
from .integration import (
    NLPIntegration,
    store_nlp_results
)

# 公开API
__all__ = [
    # 版本
    "__version__",
    
    # 连接器
    "Neo4jConnector",
    "Neo4jConnectionError",
    "get_connector",
    "connect_neo4j",
    
    # 数据模型
    "Entity",
    "EntityType",
    "Relation",
    "RelationType",
    
    # 存储
    "EntityStorage",
    "RelationStorage",
    "GraphStorage",
    
    # API
    "router",
    "GraphAPI",
    
    # 配置
    "GraphConfig",
    "load_config",
    "get_default_config",
    
    # 错误
    "GraphStorageError",
    "ConnectionError",
    "EntityNotFoundError",
    "RelationNotFoundError",
    "ValidationError",
    
    # 集成
    "NLPIntegration",
    "store_nlp_results"
]