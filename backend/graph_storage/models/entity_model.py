"""
实体数据模型

定义与NLP模块输出兼容的实体数据结构
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime
import uuid


class EntityType(str, Enum):
    """
    实体类型枚举
    
    与NLP模块的实体识别输出保持一致
    """
    PERSON = "PERSON"           # 人物
    ORG = "ORG"                  # 组织
    GPE = "GPE"                  # 地理政治实体（国家、城市等）
    LOC = "LOC"                  # 位置
    DATE = "DATE"               # 日期
    TIME = "TIME"               # 时间
    MONEY = "MONEY"             # 货币金额
    PERCENT = "PERCENT"         # 百分比
    FAC = "FAC"                  # 设施
    PRODUCT = "PRODUCT"         # 产品
    EVENT = "EVENT"             # 事件
    WORK_OF_ART = "WORK_OF_ART" # 艺术作品
    LAW = "LAW"                  # 法律
    LANGUAGE = "LANGUAGE"       # 语言
    CARDINAL = "CARDINAL"       # 基数
    ORDINAL = "ORDINAL"         # 序数
    QUANTITY = "QUANTITY"       # 数量
    UNKNOWN = "UNKNOWN"         # 未知类型
    
    @classmethod
    def from_string(cls, type_str: str) -> 'EntityType':
        """从字符串转换为EntityType"""
        try:
            return cls(type_str.upper())
        except ValueError:
            return cls.UNKNOWN


@dataclass
class Entity:
    """
    实体数据模型
    
    与NLP模块的实体识别输出格式兼容：
    {
        "text": "张三",
        "type": "PERSON",
        "start_pos": 0,
        "end_pos": 2,
        "confidence": 0.95
    }
    
    Attributes:
        id: 实体唯一标识符
        text: 实体文本
        type: 实体类型
        start_pos: 在原文中的起始位置
        end_pos: 在原文中的结束位置
        confidence: 识别置信度 (0.0-1.0)
        source_document: 来源文档标识
        metadata: 额外元数据
        created_at: 创建时间
        updated_at: 更新时间
    """
    
    text: str
    type: EntityType
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    start_pos: Optional[int] = None
    end_pos: Optional[int] = None
    confidence: float = 1.0
    source_document: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """初始化后处理"""
        # 确保type是EntityType枚举
        if isinstance(self.type, str):
            self.type = EntityType.from_string(self.type)
        
        # 确保confidence在有效范围内
        self.confidence = max(0.0, min(1.0, self.confidence))
    
    @classmethod
    def from_nlp_output(cls, nlp_entity: Dict[str, Any], source_document: Optional[str] = None) -> 'Entity':
        """
        从NLP模块输出创建实体
        
        Args:
            nlp_entity: NLP模块输出的实体字典
            source_document: 来源文档标识
            
        Returns:
            Entity: 实体对象
        """
        return cls(
            text=nlp_entity.get("text", ""),
            type=EntityType.from_string(nlp_entity.get("type", "UNKNOWN")),
            start_pos=nlp_entity.get("start_pos"),
            end_pos=nlp_entity.get("end_pos"),
            confidence=nlp_entity.get("confidence", 1.0),
            source_document=source_document,
            metadata=nlp_entity.get("metadata", {})
        )
    
    @classmethod
    def from_neo4j_node(cls, node_data: Dict[str, Any]) -> 'Entity':
        """
        从Neo4j节点数据创建实体
        
        Args:
            node_data: Neo4j节点属性字典
            
        Returns:
            Entity: 实体对象
        """
        return cls(
            id=node_data.get("id", str(uuid.uuid4())),
            text=node_data.get("text", ""),
            type=EntityType.from_string(node_data.get("type", "UNKNOWN")),
            start_pos=node_data.get("start_pos"),
            end_pos=node_data.get("end_pos"),
            confidence=node_data.get("confidence", 1.0),
            source_document=node_data.get("source_document"),
            metadata=node_data.get("metadata", {}),
            created_at=datetime.fromisoformat(node_data["created_at"]) if node_data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(node_data["updated_at"]) if node_data.get("updated_at") else datetime.now()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典（用于API响应）
        
        Returns:
            dict: 实体数据字典
        """
        return {
            "id": self.id,
            "text": self.text,
            "type": self.type.value if isinstance(self.type, EntityType) else self.type,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "confidence": self.confidence,
            "source_document": self.source_document,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_neo4j_properties(self) -> Dict[str, Any]:
        """
        转换为Neo4j节点属性
        
        Returns:
            dict: Neo4j节点属性字典
        """
        props = {
            "id": self.id,
            "text": self.text,
            "type": self.type.value if isinstance(self.type, EntityType) else self.type,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat() if self.created_at else datetime.now().isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else datetime.now().isoformat()
        }
        
        # 可选属性
        if self.start_pos is not None:
            props["start_pos"] = self.start_pos
        if self.end_pos is not None:
            props["end_pos"] = self.end_pos
        if self.source_document:
            props["source_document"] = self.source_document
        if self.metadata:
            # 将metadata转为JSON字符串存储
            import json
            props["metadata"] = json.dumps(self.metadata, ensure_ascii=False)
            
        return props
    
    def __eq__(self, other):
        """判断两个实体是否相等（基于文本和类型）"""
        if not isinstance(other, Entity):
            return False
        return self.text == other.text and self.type == other.type
    
    def __hash__(self):
        """哈希函数（基于文本和类型）"""
        return hash((self.text, self.type.value if isinstance(self.type, EntityType) else self.type))
    
    def __repr__(self):
        return f"Entity(text='{self.text}', type={self.type.value}, confidence={self.confidence})"


class EntityCollection:
    """
    实体集合类
    
    用于批量处理实体
    """
    
    def __init__(self, entities: Optional[List[Entity]] = None):
        self._entities: List[Entity] = entities or []
    
    def add(self, entity: Entity):
        """添加实体"""
        self._entities.append(entity)
    
    def add_from_nlp_output(self, nlp_entities: List[Dict[str, Any]], source_document: Optional[str] = None):
        """从NLP输出批量添加实体"""
        for nlp_entity in nlp_entities:
            self._entities.append(Entity.from_nlp_output(nlp_entity, source_document))
    
    def get_by_type(self, entity_type: EntityType) -> List[Entity]:
        """按类型筛选实体"""
        return [e for e in self._entities if e.type == entity_type]
    
    def get_unique(self) -> List[Entity]:
        """获取去重后的实体列表"""
        seen = set()
        unique = []
        for entity in self._entities:
            key = (entity.text, entity.type)
            if key not in seen:
                seen.add(key)
                unique.append(entity)
        return unique
    
    def to_list(self) -> List[Dict[str, Any]]:
        """转换为字典列表"""
        return [e.to_dict() for e in self._entities]
    
    def __iter__(self):
        return iter(self._entities)
    
    def __len__(self):
        return len(self._entities)
    
    def __getitem__(self, index):
        return self._entities[index]
