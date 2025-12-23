import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from nlp.utils.config_manager import ConfigManager
from nlp.utils.error_handler import ErrorHandler
import logging
import os
from typing import Dict, Any

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NLPService:
    """NLP服务主类"""
    
    def __init__(self, config_path: str = None):
        """
        初始化NLP服务
        
        Args:
            config_path: 配置文件路径（可选）
        """
        self.app = FastAPI(
            title="NLP Service",
            description="NLP处理服务API",
            version="1.0.0"
        )
        
        # 添加CORS中间件
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 初始化错误处理器
        self.error_handler = ErrorHandler()
        
        # 初始化模块
        self._initialize_modules()
        
        # 注册路由
        self._register_routes()
        
        logger.info("NLP服务初始化完成")
    
    def _load_config(self, config_path: str = None) -> Dict[str, Any]:
        """
        加载配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        # 默认配置
        default_config = {
            "api": {
                "host": "0.0.0.0",
                "port": 8000,
                "debug": False,
                "max_content_length": 16 * 1024 * 1024  # 16MB
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "entity_recognition": {
                "default_model": "spaCy + transformers"
            },
            "summary": {
                "default_method": "auto",
                "max_summary_length": 150,
                "min_summary_length": 30
            }
        }
        
        # 从配置文件加载
        if config_path and os.path.exists(config_path):
            config = ConfigManager.load_config(config_path)
            default_config = ConfigManager.merge_configs(default_config, config)
        
        # 从环境变量加载
        env_config = ConfigManager.get_environment_config(prefix="NLP_")
        default_config = ConfigManager.merge_configs(default_config, env_config)
        
        logger.info(f"配置加载完成，API端口: {default_config['api']['port']}")
        return default_config
    
    def _initialize_modules(self) -> None:
        """
        初始化各个模块
        """
        try:
            # 获取模块配置
            nlp_config = self.config.get('nlp', {})
            entity_config = nlp_config.get('entity_recognition', {})
            summary_config = nlp_config.get('summary', {})
            
            # 初始化实体识别模块
            from nlp.entity_recognition.entity_recognition import EntityRecognitionModel
            self.entity_recognition = EntityRecognitionModel()
            logger.info("实体识别模块初始化成功")
            
            # 初始化摘要模块
            from nlp.summary.summary_model import SummaryModel
            self.summary = SummaryModel()
            logger.info("摘要模块初始化成功")
            
        except Exception as e:
            logger.error(f"模块初始化失败: {e}")
            raise RuntimeError(f"无法初始化NLP模块: {e}")
    
    def _register_routes(self) -> None:
        """
        注册API路由
        """
        try:
            # 导入API模块
            from nlp.api.entity_api import router as entity_router
            from nlp.api.summary_api import router as summary_router
            from nlp.api.pdf_api import router as pdf_router
            
            # 注册实体识别API
            self.app.include_router(entity_router, prefix="/api/nlp/entities")
            
            # 注册摘要API
            self.app.include_router(summary_router, prefix="/api/nlp/summary")
            
            # 注册PDF处理API
            self.app.include_router(pdf_router, prefix="/api/pdf")
            
            # 注册健康检查
            @self.app.get("/health")
            def health_check():
                return {
                    "status": "healthy",
                    "timestamp": "2025-12-17T00:00:00Z",
                    "services": {
                        "entity_recognition": "running",
                        "summary": "running"
                    }
                }
            
            # 注册信息端点
            @self.app.get("/info")
            def get_info():
                return {
                    "name": "NLP Service",
                    "version": "1.0.0",
                    "description": "NLP处理服务",
                    "modules": {
                        "entity_recognition": "supported",
                        "summary": "supported"
                    }
                }
            
            logger.info("API路由注册完成")
            
        except Exception as e:
            logger.error(f"路由注册失败: {e}")
            raise RuntimeError(f"无法注册API路由: {e}")
    
    def run(self, host: str = None, port: int = None, debug: bool = None) -> None:
        """
        运行服务
        
        Args:
            host: 主机地址
            port: 端口
            debug: 调试模式
        """
        try:
            # 获取配置
            config = self.config.get('api', {})
            
            # 使用配置或参数
            host = host or config.get('host', '0.0.0.0')
            port = port or config.get('port', 8000)
            debug = debug if debug is not None else config.get('debug', False)
            
            logger.info(f"启动NLP服务，主机: {host}, 端口: {port}, 调试模式: {debug}")
            
            # 运行FastAPI应用
            import uvicorn
            uvicorn.run(
                self.app,
                host=host,
                port=port,
                debug=debug,
                workers=4  # 启用多进程
            )
            
        except Exception as e:
            logger.error(f"服务运行失败: {e}")
            raise RuntimeError(f"无法启动NLP服务: {e}")
    
    def get_app(self) -> FastAPI:
        """
        获取FastAPI应用实例
        
        Returns:
            FastAPI应用实例
        """
        return self.app
    
    def test_endpoint(self, endpoint: str, method: str = 'GET', data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        测试API端点（用于开发调试）
        
        Args:
            endpoint: 端点路径
            method: HTTP方法
            data: 请求数据
            
        Returns:
            响应数据
        """
        try:
            import httpx
            client = httpx.Client()
            
            if method.upper() == 'GET':
                response = client.get(f"http://localhost:8000{endpoint}")
            elif method.upper() == 'POST':
                response = client.post(f"http://localhost:8000{endpoint}", json=data or {})
            else:
                return {"status": "error", "message": "不支持的HTTP方法"}
            
            return {
                "status": "success",
                "status_code": response.status_code,
                "response": response.json() if response.is_success else response.text
            }
            
        except Exception as e:
            logger.error(f"端点测试失败: {e}")
            return {"status": "error", "message": str(e)}

def create_app(config_path: str = None) -> FastAPI:
    """
    创建FastAPI应用工厂函数
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        FastAPI应用实例
    """
    try:
        # 创建NLP服务实例
        nlp_service = NLPService(config_path)
        
        # 返回FastAPI应用
        return nlp_service.get_app()
        
    except Exception as e:
        logging.error(f"创建应用失败: {e}")
        raise RuntimeError(f"无法创建NLP服务应用: {e}")

if __name__ == '__main__':
    # 直接运行服务
    service = NLPService()
    service.run()
