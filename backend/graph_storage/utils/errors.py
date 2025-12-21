"""
错误处理模块

定义图数据库相关的异常类
"""

from typing import Optional, Any


class GraphStorageError(Exception):
    """
    图存储基础异常类
    
    所有图存储相关的异常都继承自此类
    """
    
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Any] = None):
        """
        初始化异常
        
        Args:
            message: 错误消息
            code: 错误代码
            details: 详细信息
        """
        self.message = message
        self.code = code
        self.details = details
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        """转换为字典（用于API响应）"""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "code": self.code,
            "details": self.details
        }


class ConnectionError(GraphStorageError):
    """
    连接错误
    
    当无法连接到Neo4j数据库时抛出
    """
    
    def __init__(self, message: str = "Failed to connect to Neo4j", details: Optional[Any] = None):
        super().__init__(message, code="CONNECTION_ERROR", details=details)


class AuthenticationError(GraphStorageError):
    """
    认证错误
    
    当Neo4j认证失败时抛出
    """
    
    def __init__(self, message: str = "Neo4j authentication failed", details: Optional[Any] = None):
        super().__init__(message, code="AUTH_ERROR", details=details)


class EntityNotFoundError(GraphStorageError):
    """
    实体未找到错误
    
    当请求的实体不存在时抛出
    """
    
    def __init__(self, entity_id: str, message: Optional[str] = None):
        msg = message or f"Entity not found: {entity_id}"
        super().__init__(msg, code="ENTITY_NOT_FOUND", details={"entity_id": entity_id})
        self.entity_id = entity_id


class RelationNotFoundError(GraphStorageError):
    """
    关系未找到错误
    
    当请求的关系不存在时抛出
    """
    
    def __init__(self, relation_id: str, message: Optional[str] = None):
        msg = message or f"Relation not found: {relation_id}"
        super().__init__(msg, code="RELATION_NOT_FOUND", details={"relation_id": relation_id})
        self.relation_id = relation_id


class ValidationError(GraphStorageError):
    """
    验证错误
    
    当输入数据验证失败时抛出
    """
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        super().__init__(message, code="VALIDATION_ERROR", details=details)
        self.field = field
        self.value = value


class QueryError(GraphStorageError):
    """
    查询错误
    
    当Cypher查询执行失败时抛出
    """
    
    def __init__(self, message: str, query: Optional[str] = None, parameters: Optional[dict] = None):
        details = {}
        if query:
            details["query"] = query
        if parameters:
            details["parameters"] = parameters
        super().__init__(message, code="QUERY_ERROR", details=details)
        self.query = query
        self.parameters = parameters


class DuplicateEntityError(GraphStorageError):
    """
    重复实体错误
    
    当尝试创建已存在的实体时抛出
    """
    
    def __init__(self, text: str, entity_type: str, message: Optional[str] = None):
        msg = message or f"Entity already exists: {text} ({entity_type})"
        super().__init__(msg, code="DUPLICATE_ENTITY", details={"text": text, "type": entity_type})
        self.text = text
        self.entity_type = entity_type


class DuplicateRelationError(GraphStorageError):
    """
    重复关系错误
    
    当尝试创建已存在的关系时抛出
    """
    
    def __init__(self, subject: str, relation: str, obj: str, message: Optional[str] = None):
        msg = message or f"Relation already exists: {subject} --[{relation}]--> {obj}"
        super().__init__(
            msg, 
            code="DUPLICATE_RELATION", 
            details={"subject": subject, "relation": relation, "object": obj}
        )
        self.subject = subject
        self.relation = relation
        self.obj = obj


class ConfigurationError(GraphStorageError):
    """
    配置错误
    
    当配置无效或缺失时抛出
    """
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        details = {"config_key": config_key} if config_key else None
        super().__init__(message, code="CONFIG_ERROR", details=details)
        self.config_key = config_key


class TransactionError(GraphStorageError):
    """
    事务错误
    
    当事务执行失败时抛出
    """
    
    def __init__(self, message: str, operation: Optional[str] = None):
        details = {"operation": operation} if operation else None
        super().__init__(message, code="TRANSACTION_ERROR", details=details)
        self.operation = operation


def handle_neo4j_exception(func):
    """
    Neo4j异常处理装饰器
    
    将Neo4j驱动异常转换为自定义异常
    """
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_type = type(e).__name__
            
            if "ServiceUnavailable" in error_type:
                raise ConnectionError(str(e), details={"original_error": error_type})
            elif "AuthError" in error_type:
                raise AuthenticationError(str(e), details={"original_error": error_type})
            elif "ConstraintError" in error_type or "Constraint" in str(e):
                raise DuplicateEntityError("Unknown", "Unknown", str(e))
            else:
                raise QueryError(str(e))
    
    return wrapper
