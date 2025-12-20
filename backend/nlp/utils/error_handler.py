import logging
from typing import Dict, Any, Optional
import traceback

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ErrorHandler:
    """错误处理工具类"""
    
    @staticmethod
    def handle_ocr_error(error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        处理OCR相关错误
        
        Args:
            error: 异常对象
            context: 错误上下文信息
            
        Returns:
            错误处理结果
        """
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "timestamp": ErrorHandler._get_timestamp(),
            "traceback": ErrorHandler._get_traceback(error)
        }
        
        # 记录错误日志
        logger.error(f"OCR错误: {error_info}")
        
        # 根据错误类型返回不同的处理结果
        if isinstance(error, FileNotFoundError):
            return {
                "status": "error",
                "message": "文件未找到",
                "details": error_info,
                "suggestion": "请检查文件路径是否正确"
            }
        elif isinstance(error, PermissionError):
            return {
                "status": "error",
                "message": "文件权限不足",
                "details": error_info,
                "suggestion": "请检查文件权限设置"
            }
        elif isinstance(error, ValueError):
            return {
                "status": "error",
                "message": "无效的输入参数",
                "details": error_info,
                "suggestion": "请检查输入参数是否正确"
            }
        else:
            return {
                "status": "error",
                "message": "OCR处理失败",
                "details": error_info,
                "suggestion": "请稍后重试或联系技术支持"
            }
    
    @staticmethod
    def handle_model_error(error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        处理模型相关错误
        
        Args:
            error: 异常对象
            context: 错误上下文信息
            
        Returns:
            错误处理结果
        """
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "timestamp": ErrorHandler._get_timestamp(),
            "traceback": ErrorHandler._get_traceback(error)
        }
        
        # 记录错误日志
        logger.error(f"模型错误: {error_info}")
        
        # 根据错误类型返回不同的处理结果
        if isinstance(error, ImportError):
            return {
                "status": "error",
                "message": "模型依赖缺失",
                "details": error_info,
                "suggestion": "请安装必要的依赖包"
            }
        elif isinstance(error, RuntimeError):
            return {
                "status": "error",
                "message": "模型运行时错误",
                "details": error_info,
                "suggestion": "请检查模型配置和输入数据"
            }
        elif isinstance(error, MemoryError):
            return {
                "status": "error",
                "message": "内存不足",
                "details": error_info,
                "suggestion": "请减少输入数据量或增加内存"
            }
        else:
            return {
                "status": "error",
                "message": "模型处理失败",
                "details": error_info,
                "suggestion": "请稍后重试或联系技术支持"
            }
    
    @staticmethod
    def handle_api_error(error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        处理API相关错误
        
        Args:
            error: 异常对象
            context: 错误上下文信息
            
        Returns:
            错误处理结果
        """
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "timestamp": ErrorHandler._get_timestamp(),
            "traceback": ErrorHandler._get_traceback(error)
        }
        
        # 记录错误日志
        logger.error(f"API错误: {error_info}")
        
        # 根据错误类型返回不同的处理结果
        if isinstance(error, ValueError):
            return {
                "status": "error",
                "message": "无效的API参数",
                "details": error_info,
                "suggestion": "请检查API参数是否正确"
            }
        elif isinstance(error, TypeError):
            return {
                "status": "error",
                "message": "API参数类型错误",
                "details": error_info,
                "suggestion": "请检查参数类型"
            }
        elif isinstance(error, AttributeError):
            return {
                "status": "error",
                "message": "API对象属性错误",
                "details": error_info,
                "suggestion": "请检查对象属性和方法"
            }
        else:
            return {
                "status": "error",
                "message": "API处理失败",
                "details": error_info,
                "suggestion": "请稍后重试或联系技术支持"
            }
    
    @staticmethod
    def handle_file_error(error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        处理文件相关错误
        
        Args:
            error: 异常对象
            context: 错误上下文信息
            
        Returns:
            错误处理结果
        """
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "timestamp": ErrorHandler._get_timestamp(),
            "traceback": ErrorHandler._get_traceback(error)
        }
        
        # 记录错误日志
        logger.error(f"文件错误: {error_info}")
        
        # 根据错误类型返回不同的处理结果
        if isinstance(error, FileNotFoundError):
            return {
                "status": "error",
                "message": "文件未找到",
                "details": error_info,
                "suggestion": "请检查文件路径是否正确"
            }
        elif isinstance(error, PermissionError):
            return {
                "status": "error",
                "message": "文件权限不足",
                "details": error_info,
                "suggestion": "请检查文件权限设置"
            }
        elif isinstance(error, IsADirectoryError):
            return {
                "status": "error",
                "message": "路径是目录而不是文件",
                "details": error_info,
                "suggestion": "请提供正确的文件路径"
            }
        elif isinstance(error, OSError):
            return {
                "status": "error",
                "message": "文件操作失败",
                "details": error_info,
                "suggestion": "请检查文件系统状态"
            }
        else:
            return {
                "status": "error",
                "message": "文件处理失败",
                "details": error_info,
                "suggestion": "请稍后重试或联系技术支持"
            }
    
    @staticmethod
    def log_error(error: Exception, context: Dict[str, Any] = None, level: str = "error") -> None:
        """
        记录错误日志
        
        Args:
            error: 异常对象
            context: 错误上下文信息
            level: 日志级别
        """
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "timestamp": ErrorHandler._get_timestamp(),
            "traceback": ErrorHandler._get_traceback(error)
        }
        
        # 根据级别记录日志
        if level == "critical":
            logger.critical(f"严重错误: {error_info}")
        elif level == "warning":
            logger.warning(f"警告: {error_info}")
        else:
            logger.error(f"错误: {error_info}")
    
    @staticmethod
    def _get_timestamp() -> str:
        """获取当前时间戳"""
        import datetime
        return datetime.datetime.now().isoformat()
    
    @staticmethod
    def _get_traceback(error: Exception) -> Optional[str]:
        """获取异常堆栈跟踪"""
        try:
            return traceback.format_exc()
        except:
            return None
    
    @staticmethod
    def create_error_response(error: Exception, context: Dict[str, Any] = None, 
                           error_type: str = "general") -> Dict[str, Any]:
        """
        创建标准化的错误响应
        
        Args:
            error: 异常对象
            context: 错误上下文信息
            error_type: 错误类型
            
        Returns:
            标准化错误响应
        """
        error_handlers = {
            "ocr": ErrorHandler.handle_ocr_error,
            "model": ErrorHandler.handle_model_error,
            "api": ErrorHandler.handle_api_error,
            "file": ErrorHandler.handle_file_error,
            "general": lambda e, c: ErrorHandler.handle_api_error(e, c)
        }
        
        handler = error_handlers.get(error_type, ErrorHandler.handle_api_error)
        return handler(error, context)
    
    @staticmethod
    def is_recoverable_error(error: Exception) -> bool:
        """
        判断错误是否可恢复
        
        Args:
            error: 异常对象
            
        Returns:
            是否可恢复
        """
        recoverable_errors = (
            ValueError, TypeError, AttributeError, 
            FileNotFoundError, PermissionError, IsADirectoryError
        )
        
        return isinstance(error, recoverable_errors)
    
    @staticmethod
    def should_retry(error: Exception, max_retries: int = 3, current_retries: int = 0) -> bool:
        """
        判断是否应该重试
        
        Args:
            error: 异常对象
            max_retries: 最大重试次数
            current_retries: 当前重试次数
            
        Returns:
            是否应该重试
        """
        if current_retries >= max_retries:
            return False
        
        # 可恢复的错误可以重试
        if ErrorHandler.is_recoverable_error(error):
            return True
        
        # 网络相关的错误可以重试
        if isinstance(error, (ConnectionError, TimeoutError)):
            return True
        
        return False
    
    @staticmethod
    def get_error_suggestion(error: Exception) -> str:
        """
        获取错误建议
        
        Args:
            error: 异常对象
            
        Returns:
            错误建议
        """
        error_suggestions = {
            FileNotFoundError: "请检查文件路径是否正确",
            PermissionError: "请检查文件权限设置",
            ValueError: "请检查输入参数是否正确",
            ImportError: "请安装必要的依赖包",
            RuntimeError: "请检查模型配置和输入数据",
            MemoryError: "请减少输入数据量或增加内存",
            ConnectionError: "请检查网络连接",
            TimeoutError: "请稍后重试"
        }
        
        return error_suggestions.get(type(error), "请稍后重试或联系技术支持")



