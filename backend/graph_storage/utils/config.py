"""
配置管理模块

提供图数据库配置管理功能
"""

import os
import json
import yaml
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Neo4jConfig:
    """Neo4j连接配置"""
    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: str = "password"
    database: str = "neo4j"
    max_connection_pool_size: int = 50
    connection_timeout: float = 30.0
    encrypted: bool = False


@dataclass
class GraphConfig:
    """
    图存储配置
    
    支持从环境变量、配置文件加载配置
    """
    
    neo4j: Neo4jConfig = field(default_factory=Neo4jConfig)
    auto_connect: bool = False
    create_indexes_on_startup: bool = True
    log_level: str = "INFO"
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'GraphConfig':
        """
        从字典创建配置
        
        Args:
            config_dict: 配置字典
            
        Returns:
            GraphConfig: 配置对象
        """
        neo4j_config = config_dict.get("neo4j", {})
        
        return cls(
            neo4j=Neo4jConfig(
                uri=neo4j_config.get("uri", "bolt://localhost:7687"),
                user=neo4j_config.get("user", "neo4j"),
                password=neo4j_config.get("password", "password"),
                database=neo4j_config.get("database", "neo4j"),
                max_connection_pool_size=neo4j_config.get("max_connection_pool_size", 50),
                connection_timeout=neo4j_config.get("connection_timeout", 30.0),
                encrypted=neo4j_config.get("encrypted", False)
            ),
            auto_connect=config_dict.get("auto_connect", False),
            create_indexes_on_startup=config_dict.get("create_indexes_on_startup", True),
            log_level=config_dict.get("log_level", "INFO")
        )
    
    @classmethod
    def from_env(cls) -> 'GraphConfig':
        """
        从环境变量创建配置
        
        环境变量:
        - NEO4J_URI: Neo4j连接URI
        - NEO4J_USER: 用户名
        - NEO4J_PASSWORD: 密码
        - NEO4J_DATABASE: 数据库名
        - GRAPH_AUTO_CONNECT: 是否自动连接
        - GRAPH_LOG_LEVEL: 日志级别
        
        Returns:
            GraphConfig: 配置对象
        """
        return cls(
            neo4j=Neo4jConfig(
                uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                user=os.getenv("NEO4J_USER", "neo4j"),
                password=os.getenv("NEO4J_PASSWORD", "password"),
                database=os.getenv("NEO4J_DATABASE", "neo4j"),
                max_connection_pool_size=int(os.getenv("NEO4J_MAX_POOL_SIZE", "50")),
                connection_timeout=float(os.getenv("NEO4J_TIMEOUT", "30.0")),
                encrypted=os.getenv("NEO4J_ENCRYPTED", "false").lower() == "true"
            ),
            auto_connect=os.getenv("GRAPH_AUTO_CONNECT", "false").lower() == "true",
            create_indexes_on_startup=os.getenv("GRAPH_CREATE_INDEXES", "true").lower() == "true",
            log_level=os.getenv("GRAPH_LOG_LEVEL", "INFO")
        )
    
    @classmethod
    def from_file(cls, file_path: str) -> 'GraphConfig':
        """
        从配置文件加载配置
        
        支持JSON和YAML格式
        
        Args:
            file_path: 配置文件路径
            
        Returns:
            GraphConfig: 配置对象
        """
        path = Path(file_path)
        
        if not path.exists():
            logger.warning(f"Config file not found: {file_path}, using defaults")
            return cls()
        
        with open(path, 'r', encoding='utf-8') as f:
            if path.suffix in ['.yaml', '.yml']:
                config_dict = yaml.safe_load(f)
            else:
                config_dict = json.load(f)
        
        # 提取graph_storage部分（如果存在）
        if "graph_storage" in config_dict:
            config_dict = config_dict["graph_storage"]
        
        return cls.from_dict(config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            dict: 配置字典
        """
        return {
            "neo4j": asdict(self.neo4j),
            "auto_connect": self.auto_connect,
            "create_indexes_on_startup": self.create_indexes_on_startup,
            "log_level": self.log_level
        }
    
    def save_to_file(self, file_path: str):
        """
        保存配置到文件
        
        Args:
            file_path: 配置文件路径
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        config_dict = self.to_dict()
        
        with open(path, 'w', encoding='utf-8') as f:
            if path.suffix in ['.yaml', '.yml']:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
            else:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Config saved to: {file_path}")
    
    def get_neo4j_connection_params(self) -> Dict[str, Any]:
        """
        获取Neo4j连接参数
        
        Returns:
            dict: 连接参数字典
        """
        return {
            "uri": self.neo4j.uri,
            "user": self.neo4j.user,
            "password": self.neo4j.password,
            "database": self.neo4j.database,
            "max_connection_pool_size": self.neo4j.max_connection_pool_size,
            "connection_timeout": self.neo4j.connection_timeout
        }


def load_config(
    file_path: Optional[str] = None,
    use_env: bool = True
) -> GraphConfig:
    """
    加载配置
    
    优先级: 环境变量 > 配置文件 > 默认值
    
    Args:
        file_path: 配置文件路径
        use_env: 是否使用环境变量
        
    Returns:
        GraphConfig: 配置对象
    """
    # 从默认配置开始
    config = GraphConfig()
    
    # 如果指定了配置文件，加载它
    if file_path:
        config = GraphConfig.from_file(file_path)
    else:
        # 尝试从默认位置加载
        default_paths = [
            "config/graph_storage.yaml",
            "config/graph_storage.json",
            "../deployment_config.yaml"
        ]
        for default_path in default_paths:
            if Path(default_path).exists():
                config = GraphConfig.from_file(default_path)
                break
    
    # 用环境变量覆盖
    if use_env:
        env_config = GraphConfig.from_env()
        
        # 只覆盖非默认值
        if os.getenv("NEO4J_URI"):
            config.neo4j.uri = env_config.neo4j.uri
        if os.getenv("NEO4J_USER"):
            config.neo4j.user = env_config.neo4j.user
        if os.getenv("NEO4J_PASSWORD"):
            config.neo4j.password = env_config.neo4j.password
        if os.getenv("NEO4J_DATABASE"):
            config.neo4j.database = env_config.neo4j.database
        if os.getenv("GRAPH_AUTO_CONNECT"):
            config.auto_connect = env_config.auto_connect
        if os.getenv("GRAPH_LOG_LEVEL"):
            config.log_level = env_config.log_level
    
    return config


def get_default_config() -> GraphConfig:
    """
    获取默认配置
    
    Returns:
        GraphConfig: 默认配置对象
    """
    return GraphConfig()


# 全局配置实例
_config: Optional[GraphConfig] = None


def get_config() -> GraphConfig:
    """
    获取全局配置实例
    
    Returns:
        GraphConfig: 配置对象
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config


def set_config(config: GraphConfig):
    """
    设置全局配置实例
    
    Args:
        config: 配置对象
    """
    global _config
    _config = config
