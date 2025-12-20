import json
import yaml
import os
import logging
from typing import Dict, Any, Optional, Union, List

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfigManager:
    """配置管理工具类"""
    
    @staticmethod
    def load_json_config(file_path: str) -> Dict[str, Any]:
        """
        加载JSON配置文件
        
        Args:
            file_path: 配置文件路径
            
        Returns:
            配置字典
        """
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            logger.error(f"JSON配置文件不存在: {file_path}")
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
            
            logger.info(f"成功加载JSON配置文件: {file_path}")
            return config
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON配置文件解析错误: {e}")
            return {}
        except Exception as e:
            logger.error(f"加载JSON配置文件失败: {e}")
            return {}
    
    @staticmethod
    def load_yaml_config(file_path: str) -> Dict[str, Any]:
        """
        加载YAML配置文件
        
        Args:
            file_path: 配置文件路径
            
        Returns:
            配置字典
        """
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            logger.error(f"YAML配置文件不存在: {file_path}")
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
            
            logger.info(f"成功加载YAML配置文件: {file_path}")
            return config or {}
            
        except yaml.YAMLError as e:
            logger.error(f"YAML配置文件解析错误: {e}")
            return {}
        except Exception as e:
            logger.error(f"加载YAML配置文件失败: {e}")
            return {}
    
    @staticmethod
    def load_config(file_path: str) -> Dict[str, Any]:
        """
        加载配置文件（自动检测格式）
        
        Args:
            file_path: 配置文件路径
            
        Returns:
            配置字典
        """
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            logger.error(f"配置文件不存在: {file_path}")
            return {}
        
        try:
            # 根据文件扩展名判断格式
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext == '.json':
                return ConfigManager.load_json_config(file_path)
            elif ext in ['.yaml', '.yml']:
                return ConfigManager.load_yaml_config(file_path)
            else:
                logger.error(f"不支持的配置文件格式: {ext}")
                return {}
                
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {}
    
    @staticmethod
    def save_json_config(config: Dict[str, Any], file_path: str) -> bool:
        """
        保存JSON配置文件
        
        Args:
            config: 配置字典
            file_path: 保存路径
            
        Returns:
            是否成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(config, file, indent=2, ensure_ascii=False)
            
            logger.info(f"成功保存JSON配置文件: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存JSON配置文件失败: {e}")
            return False
    
    @staticmethod
    def save_yaml_config(config: Dict[str, Any], file_path: str) -> bool:
        """
        保存YAML配置文件
        
        Args:
            config: 配置字典
            file_path: 保存路径
            
        Returns:
            是否成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as file:
                yaml.dump(config, file, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"成功保存YAML配置文件: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存YAML配置文件失败: {e}")
            return False
    
    @staticmethod
    def get_config_value(config: Dict[str, Any], key: str, default: Any = None) -> Any:
        """
        获取配置值（支持嵌套键）
        
        Args:
            config: 配置字典
            key: 配置键（支持点号分隔的嵌套键，如"database.host"）
            default: 默认值
            
        Returns:
            配置值
        """
        try:
            keys = key.split('.')
            value = config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
            
        except Exception:
            return default
    
    @staticmethod
    def set_config_value(config: Dict[str, Any], key: str, value: Any) -> bool:
        """
        设置配置值（支持嵌套键）
        
        Args:
            config: 配置字典
            key: 配置键（支持点号分隔的嵌套键）
            value: 配置值
            
        Returns:
            是否成功
        """
        try:
            keys = key.split('.')
            current = config
            
            # 遍历到倒数第二个键
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            
            # 设置最后一个键的值
            current[keys[-1]] = value
            return True
            
        except Exception as e:
            logger.error(f"设置配置值失败: {e}")
            return False
    
    @staticmethod
    def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
        """
        合并多个配置
        
        Args:
            *configs: 多个配置字典
            
        Returns:
            合并后的配置
        """
        merged_config = {}
        
        for config in configs:
            if isinstance(config, dict):
                merged_config.update(config)
        
        logger.info(f"合并配置完成，共合并 {len(configs)} 个配置")
        return merged_config
    
    @staticmethod
    def validate_config(config: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """
        验证配置是否符合schema
        
        Args:
            config: 配置字典
            schema: 配置schema
            
        Returns:
            是否有效
        """
        try:
            for key, value_type in schema.items():
                if key not in config:
                    logger.warning(f"配置缺少必需的键: {key}")
                    return False
                
                if not isinstance(config[key], value_type):
                    logger.warning(f"配置键 {key} 的类型不匹配，期望 {value_type}，实际 {type(config[key])}")
                    return False
            
            logger.info("配置验证通过")
            return True
            
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return False
    
    @staticmethod
    def get_environment_config(prefix: str = "NLP_") -> Dict[str, Any]:
        """
        从环境变量获取配置
        
        Args:
            prefix: 环境变量前缀
            
        Returns:
            环境变量配置
        """
        config = {}
        
        try:
            import os
            for key, value in os.environ.items():
                if key.startswith(prefix):
                    # 转换环境变量名为配置键名
                    config_key = key[len(prefix):].lower().replace('_', '.')
                    config[config_key] = value
            
            logger.info(f"从环境变量获取配置，找到 {len(config)} 个配置项")
            return config
            
        except Exception as e:
            logger.error(f"从环境变量获取配置失败: {e}")
            return {}
    
    @staticmethod
    def create_default_config() -> Dict[str, Any]:
        """
        创建默认配置
        
        Returns:
            默认配置
        """
        default_config = {
            "ocr": {
                "tesseract_path": "",
                "default_ocr_mode": "auto",
                "max_file_size": 16 * 1024 * 1024,  # 16MB
                "supported_formats": ["pdf", "png", "jpg", "jpeg", "bmp", "tiff"]
            },
            "summary": {
                "default_method": "auto",
                "max_summary_length": 150,
                "min_summary_length": 30,
                "supported_methods": ["bart", "textrank", "auto"]
            },
            "entity_recognition": {
                "default_model": "spaCy + transformers",
                "supported_entity_types": ["PERSON", "ORG", "DATE", "LOCATION", "MONEY", "PERCENT"]
            },
            "api": {
                "host": "0.0.0.0",
                "port": 5000,
                "debug": False,
                "max_content_length": 16 * 1024 * 1024  # 16MB
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "nlp_service.log"
            },
            "cache": {
                "enabled": True,
                "max_size": 100,  # 最大缓存项数
                "ttl": 3600  # 缓存过期时间（秒）
            }
        }
        
        logger.info("创建默认配置")
        return default_config
    
    @staticmethod
    def load_config_from_multiple_sources(sources: List[Union[str, Dict[str, Any]]]) -> Dict[str, Any]:
        """
        从多个来源加载配置并合并
        
        Args:
            sources: 配置来源列表（文件路径或配置字典）
            
        Returns:
            合并后的配置
        """
        configs = []
        
        for source in sources:
            if isinstance(source, str):
                # 从文件加载
                config = ConfigManager.load_config(source)
                configs.append(config)
            elif isinstance(source, dict):
                # 直接使用配置字典
                configs.append(source)
            else:
                logger.warning(f"不支持的配置来源类型: {type(source)}")
        
        # 合并所有配置
        merged_config = ConfigManager.merge_configs(*configs)
        
        # 添加默认配置（如果需要）
        if not merged_config:
            merged_config = ConfigManager.create_default_config()
        
        logger.info(f"从多个来源加载配置，共合并 {len(configs)} 个配置")
        return merged_config
    
    @staticmethod
    def get_config_schema() -> Dict[str, Any]:
        """
        获取配置schema
        
        Returns:
            配置schema
        """
        schema = {
            "ocr": dict,
            "summary": dict,
            "entity_recognition": dict,
            "api": dict,
            "logging": dict,
            "cache": dict
        }
        
        logger.info("获取配置schema")
        return schema
    
    @staticmethod
    def update_config_file(config: Dict[str, Any], file_path: str, format: str = "json") -> bool:
        """
        更新配置文件
        
        Args:
            config: 配置字典
            file_path: 文件路径
            format: 文件格式（json/yaml）
            
        Returns:
            是否成功
        """
        try:
            if format.lower() == "json":
                return ConfigManager.save_json_config(config, file_path)
            elif format.lower() in ["yaml", "yml"]:
                return ConfigManager.save_yaml_config(config, file_path)
            else:
                logger.error(f"不支持的配置文件格式: {format}")
                return False
                
        except Exception as e:
            logger.error(f"更新配置文件失败: {e}")
            return False
    
    @staticmethod
    def get_config_difference(config1: Dict[str, Any], config2: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取两个配置的差异
        
        Args:
            config1: 第一个配置
            config2: 第二个配置
            
        Returns:
            配置差异
        """
        difference = {}
        
        try:
            for key in set(config1.keys()).union(set(config2.keys())):
                if key not in config1:
                    difference[key] = {"old": None, "new": config2[key]}
                elif key not in config2:
                    difference[key] = {"old": config1[key], "new": None}
                elif config1[key] != config2[key]:
                    difference[key] = {"old": config1[key], "new": config2[key]}
            
            logger.info(f"获取配置差异，共 {len(difference)} 个差异项")
            return difference
            
        except Exception as e:
            logger.error(f"获取配置差异失败: {e}")
            return {}


