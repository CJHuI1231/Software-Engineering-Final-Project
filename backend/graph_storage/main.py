"""
Graph Storage 主入口

提供FastAPI应用和启动配置
"""

import logging
import os
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import router
from .neo4j_connector import get_connector
from .utils.config import load_config, GraphConfig

logger = logging.getLogger(__name__)


def create_app(
    config: Optional[GraphConfig] = None,
    include_nlp_router: bool = False
) -> FastAPI:
    """
    创建FastAPI应用
    
    Args:
        config: 配置对象
        include_nlp_router: 是否包含NLP路由（用于集成部署）
        
    Returns:
        FastAPI: 应用实例
    """
    # 加载配置
    if config is None:
        config = load_config()
    
    # 设置日志级别
    logging.basicConfig(level=getattr(logging, config.log_level.upper(), logging.INFO))
    
    # 创建应用
    app = FastAPI(
        title="Graph Storage API",
        description="Neo4j图数据库集成API，用于存储和查询命名实体及其关系",
        version="1.0.0",
        docs_url="/graph/docs",
        redoc_url="/graph/redoc",
        openapi_url="/graph/openapi.json"
    )
    
    # CORS配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册路由
    app.include_router(router)
    
    # 可选：包含NLP路由
    if include_nlp_router:
        try:
            from ..nlp.api.entity_api import router as entity_router
            from ..nlp.api.summary_api import router as summary_router
            app.include_router(entity_router)
            app.include_router(summary_router)
            logger.info("NLP routers included")
        except ImportError:
            logger.warning("NLP module not found, skipping NLP routers")
    
    # 启动事件
    @app.on_event("startup")
    async def startup_event():
        logger.info("Graph Storage API starting...")
        
        # 自动连接（如果配置中启用）
        if config.auto_connect:
            try:
                connector = get_connector()
                connector.connect_from_config(config.get_neo4j_connection_params())
                logger.info("Auto-connected to Neo4j")
                
                # 创建索引
                if config.create_indexes_on_startup:
                    from .storage import GraphStorage
                    storage = GraphStorage(connector)
                    storage.create_indexes()
                    logger.info("Indexes created")
            except Exception as e:
                logger.error(f"Failed to auto-connect to Neo4j: {e}")
    
    # 关闭事件
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Graph Storage API shutting down...")
        connector = get_connector()
        if connector.is_connected:
            connector.close()
            logger.info("Neo4j connection closed")
    
    # 根路由
    @app.get("/")
    async def root():
        return {
            "service": "Graph Storage API",
            "version": "1.0.0",
            "docs": "/graph/docs"
        }
    
    return app


def run_standalone(
    host: str = "0.0.0.0",
    port: int = 8001,
    reload: bool = False
):
    """
    独立运行Graph Storage服务
    
    Args:
        host: 主机地址
        port: 端口号
        reload: 是否启用热重载
    """
    import uvicorn
    
    uvicorn.run(
        "backend.graph_storage.main:create_app",
        host=host,
        port=port,
        reload=reload,
        factory=True
    )


# 默认应用实例（用于uvicorn直接运行）
app = create_app()


if __name__ == "__main__":
    run_standalone(reload=True)
