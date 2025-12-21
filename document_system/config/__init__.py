"""
配置模块

提供数据库连接配置和相关工具函数
"""

from .database import DB_CONFIG, DatabaseConnection, generate_user_id

__all__ = [
    'DB_CONFIG',
    'DatabaseConnection', 
    'generate_user_id'
]
