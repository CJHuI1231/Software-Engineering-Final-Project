"""
集成层模块
连接NLP/OCR处理模块与MySQL数据库存储
"""

from .db_integration import DatabaseIntegration

__all__ = ['DatabaseIntegration']
