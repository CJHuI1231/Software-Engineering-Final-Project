"""
Neo4j数据库连接管理模块

提供Neo4j数据库的连接管理功能，包括：
- 单例模式连接管理
- 连接池配置
- 健康检查
- 会话管理
"""

import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager
import threading

try:
    from neo4j import GraphDatabase, Driver, Session
    from neo4j.exceptions import ServiceUnavailable, AuthError, ConfigurationError
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    GraphDatabase = None
    Driver = None
    Session = None

logger = logging.getLogger(__name__)


class Neo4jConnectionError(Exception):
    """Neo4j连接错误"""
    pass


class Neo4jConnector:
    """
    Neo4j数据库连接器（单例模式）
    
    支持手动配置连接设置或通过Docker启动服务
    
    使用示例:
        # 初始化连接
        connector = Neo4jConnector.get_instance()
        connector.connect(uri="bolt://localhost:7687", user="neo4j", password="password")
        
        # 使用会话执行查询
        with connector.get_session() as session:
            result = session.run("MATCH (n) RETURN n LIMIT 10")
            
        # 关闭连接
        connector.close()
    """
    
    _instance: Optional['Neo4jConnector'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._driver: Optional[Driver] = None
        self._config: Dict[str, Any] = {}
        self._connected = False
        self._initialized = True
        
    @classmethod
    def get_instance(cls) -> 'Neo4jConnector':
        """获取连接器单例实例"""
        return cls()
    
    @classmethod
    def reset_instance(cls):
        """重置单例实例（主要用于测试）"""
        with cls._lock:
            if cls._instance is not None:
                cls._instance.close()
                cls._instance = None
    
    def connect(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "password",
        database: str = "neo4j",
        max_connection_pool_size: int = 50,
        connection_timeout: float = 30.0,
        **kwargs
    ) -> bool:
        """
        建立Neo4j数据库连接
        
        Args:
            uri: Neo4j连接URI (bolt://host:port)
            user: 用户名
            password: 密码
            database: 数据库名称
            max_connection_pool_size: 连接池最大连接数
            connection_timeout: 连接超时时间（秒）
            **kwargs: 其他Neo4j驱动参数
            
        Returns:
            bool: 连接是否成功
            
        Raises:
            Neo4jConnectionError: 连接失败时抛出
        """
        if not NEO4J_AVAILABLE:
            raise Neo4jConnectionError(
                "Neo4j driver not installed. Please install it with: pip install neo4j"
            )
        
        try:
            # 关闭现有连接
            if self._driver is not None:
                self.close()
            
            # 创建驱动
            self._driver = GraphDatabase.driver(
                uri,
                auth=(user, password),
                max_connection_pool_size=max_connection_pool_size,
                connection_timeout=connection_timeout,
                **kwargs
            )
            
            # 验证连接
            self._driver.verify_connectivity()
            
            # 保存配置
            self._config = {
                "uri": uri,
                "user": user,
                "database": database,
                "max_connection_pool_size": max_connection_pool_size,
                "connection_timeout": connection_timeout
            }
            
            self._connected = True
            logger.info(f"Successfully connected to Neo4j at {uri}")
            return True
            
        except AuthError as e:
            logger.error(f"Neo4j authentication failed: {e}")
            raise Neo4jConnectionError(f"Authentication failed: {e}")
        except ServiceUnavailable as e:
            logger.error(f"Neo4j service unavailable: {e}")
            raise Neo4jConnectionError(f"Service unavailable: {e}")
        except ConfigurationError as e:
            logger.error(f"Neo4j configuration error: {e}")
            raise Neo4jConnectionError(f"Configuration error: {e}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise Neo4jConnectionError(f"Connection failed: {e}")
    
    def connect_from_config(self, config: Dict[str, Any]) -> bool:
        """
        从配置字典建立连接
        
        Args:
            config: 包含连接参数的配置字典
            
        Returns:
            bool: 连接是否成功
        """
        return self.connect(
            uri=config.get("uri", "bolt://localhost:7687"),
            user=config.get("user", "neo4j"),
            password=config.get("password", "password"),
            database=config.get("database", "neo4j"),
            max_connection_pool_size=config.get("max_connection_pool_size", 50),
            connection_timeout=config.get("connection_timeout", 30.0)
        )
    
    @contextmanager
    def get_session(self, database: Optional[str] = None):
        """
        获取数据库会话（上下文管理器）
        
        Args:
            database: 数据库名称，默认使用连接时指定的数据库
            
        Yields:
            Session: Neo4j会话对象
            
        Raises:
            Neo4jConnectionError: 未连接时抛出
        """
        if not self._connected or self._driver is None:
            raise Neo4jConnectionError("Not connected to Neo4j. Please call connect() first.")
        
        db = database or self._config.get("database", "neo4j")
        session = self._driver.session(database=db)
        try:
            yield session
        finally:
            session.close()
    
    def execute_query(
        self, 
        query: str, 
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> list:
        """
        执行Cypher查询
        
        Args:
            query: Cypher查询语句
            parameters: 查询参数
            database: 数据库名称
            
        Returns:
            list: 查询结果列表
        """
        with self.get_session(database) as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]
    
    def execute_write(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> Any:
        """
        执行写入操作（事务）
        
        Args:
            query: Cypher写入语句
            parameters: 查询参数
            database: 数据库名称
            
        Returns:
            写入操作的结果
        """
        def _write_tx(tx, query, parameters):
            result = tx.run(query, parameters or {})
            return result.consume()
        
        with self.get_session(database) as session:
            return session.execute_write(_write_tx, query, parameters)
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            dict: 包含连接状态和服务器信息的字典
        """
        health_status = {
            "connected": self._connected,
            "neo4j_available": NEO4J_AVAILABLE,
            "config": {
                "uri": self._config.get("uri"),
                "database": self._config.get("database")
            } if self._config else None
        }
        
        if self._connected and self._driver is not None:
            try:
                self._driver.verify_connectivity()
                health_status["status"] = "healthy"
                
                # 获取服务器信息
                with self.get_session() as session:
                    result = session.run("CALL dbms.components()")
                    components = [record.data() for record in result]
                    if components:
                        health_status["server_info"] = components[0]
                        
            except Exception as e:
                health_status["status"] = "unhealthy"
                health_status["error"] = str(e)
        else:
            health_status["status"] = "disconnected"
            
        return health_status
    
    def close(self):
        """关闭数据库连接"""
        if self._driver is not None:
            try:
                self._driver.close()
                logger.info("Neo4j connection closed")
            except Exception as e:
                logger.error(f"Error closing Neo4j connection: {e}")
            finally:
                self._driver = None
                self._connected = False
                self._config = {}
    
    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected
    
    @property
    def driver(self) -> Optional[Driver]:
        """获取底层驱动（高级用法）"""
        return self._driver
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# 便捷函数
def get_connector() -> Neo4jConnector:
    """获取Neo4j连接器实例"""
    return Neo4jConnector.get_instance()


def connect_neo4j(
    uri: str = "bolt://localhost:7687",
    user: str = "neo4j",
    password: str = "password",
    **kwargs
) -> Neo4jConnector:
    """
    便捷函数：连接到Neo4j数据库
    
    Args:
        uri: 连接URI
        user: 用户名
        password: 密码
        **kwargs: 其他参数
        
    Returns:
        Neo4jConnector: 已连接的连接器实例
    """
    connector = get_connector()
    connector.connect(uri=uri, user=user, password=password, **kwargs)
    return connector
