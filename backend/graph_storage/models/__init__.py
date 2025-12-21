"""
图数据库数据模型

提供实体和关系的数据模型定义
"""

from .entity_model import Entity, EntityType
from .relation_model import Relation, RelationType

__all__ = [
    "Entity",
    "EntityType", 
    "Relation",
    "RelationType"
]
