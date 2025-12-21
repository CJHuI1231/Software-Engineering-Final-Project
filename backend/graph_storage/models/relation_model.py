"""
关系数据模型

定义与NLP模块输出兼容的关系数据结构
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid


# 常见关系类型常量（仅供参考，不强制使用）
class CommonRelationTypes:
    """
    常见关系类型常量
    
    这些只是参考值，实际使用时可以使用任意字符串作为关系类型
    """
    # 人物关系
    WORKS_AT = "works_at"           # 工作于
    LIVES_IN = "lives_in"           # 居住于
    BORN_IN = "born_in"             # 出生于
    STUDIED_AT = "studied_at"       # 就读于
    MARRIED_TO = "married_to"       # 配偶
    PARENT_OF = "parent_of"         # 父母
    CHILD_OF = "child_of"           # 子女
    SIBLING_OF = "sibling_of"       # 兄弟姐妹
    COLLEAGUE_OF = "colleague_of"   # 同事
    FRIEND_OF = "friend_of"         # 朋友
    
    # 组织关系
    LOCATED_IN = "located_in"       # 位于
    PART_OF = "part_of"             # 属于
    OWNS = "owns"                   # 拥有
    OWNED_BY = "owned_by"           # 被拥有
    SUBSIDIARY_OF = "subsidiary_of" # 子公司
    FOUNDED_BY = "founded_by"       # 创立者
    CEO_OF = "ceo_of"               # CEO
    MEMBER_OF = "member_of"         # 成员
    
    # 事件关系
    PARTICIPATED_IN = "participated_in"  # 参与
    OCCURRED_AT = "occurred_at"          # 发生于
    OCCURRED_ON = "occurred_on"          # 发生在（时间）
    CAUSED_BY = "caused_by"              # 由...引起
    RESULTED_IN = "resulted_in"          # 导致
    
    # 通用关系
    RELATED_TO = "related_to"       # 相关
    MENTIONED_WITH = "mentioned_with"  # 共同提及
    ASSOCIATED_WITH = "associated_with"  # 关联


# 为了向后兼容，保留RelationType作为CommonRelationTypes的别名
RelationType = CommonRelationTypes


@dataclass
class Relation:
    """
    关系数据模型
    
    与NLP模块的关系提取输出格式兼容：
    {
        "subject": "张三",
        "relation": "works_at",
        "object": "阿里巴巴",
        "confidence": 0.8
    }
    
    注意：relation字段接受任意字符串，NLP提取出的关系类型会被直接使用，
    不会经过枚举类过滤。
    
    Attributes:
        id: 关系唯一标识符
        subject: 主体实体文本
        subject_id: 主体实体ID（在图数据库中）
        relation: 关系类型（任意字符串）
        object: 客体实体文本
        object_id: 客体实体ID（在图数据库中）
        confidence: 关系置信度 (0.0-1.0)
        source_document: 来源文档标识
        metadata: 额外元数据
        created_at: 创建时间
        updated_at: 更新时间
    """
    
    subject: str
    relation: str  # 改为直接使用字符串，支持任意关系类型
    object: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    subject_id: Optional[str] = None
    object_id: Optional[str] = None
    confidence: float = 1.0
    source_document: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """初始化后处理"""
        # 确保relation是字符串
        if not isinstance(self.relation, str):
            self.relation = str(self.relation)
        
        # 标准化关系类型（小写，去除首尾空格）
        self.relation = self.relation.strip().lower()
        
        # 确保confidence在有效范围内
        self.confidence = max(0.0, min(1.0, self.confidence))
    
    @classmethod
    def from_nlp_output(cls, nlp_relation: Dict[str, Any], source_document: Optional[str] = None) -> 'Relation':
        """
        从NLP模块输出创建关系
        
        Args:
            nlp_relation: NLP模块输出的关系字典
            source_document: 来源文档标识
            
        Returns:
            Relation: 关系对象
        """
        return cls(
            subject=nlp_relation.get("subject", ""),
            relation=nlp_relation.get("relation", "related_to"),  # 默认使用通用关系
            object=nlp_relation.get("object", ""),
            confidence=nlp_relation.get("confidence", 1.0),
            source_document=source_document,
            metadata=nlp_relation.get("metadata", {})
        )
    
    @classmethod
    def from_neo4j_relationship(cls, rel_data: Dict[str, Any]) -> 'Relation':
        """
        从Neo4j关系数据创建Relation对象
        
        Args:
            rel_data: Neo4j关系属性字典
            
        Returns:
            Relation: 关系对象
        """
        return cls(
            id=rel_data.get("id", str(uuid.uuid4())),
            subject=rel_data.get("subject", ""),
            subject_id=rel_data.get("subject_id"),
            relation=rel_data.get("relation", "related_to"),
            object=rel_data.get("object", ""),
            object_id=rel_data.get("object_id"),
            confidence=rel_data.get("confidence", 1.0),
            source_document=rel_data.get("source_document"),
            metadata=rel_data.get("metadata", {}),
            created_at=datetime.fromisoformat(rel_data["created_at"]) if rel_data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(rel_data["updated_at"]) if rel_data.get("updated_at") else datetime.now()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典（用于API响应）
        
        Returns:
            dict: 关系数据字典
        """
        return {
            "id": self.id,
            "subject": self.subject,
            "subject_id": self.subject_id,
            "relation": self.relation,
            "object": self.object,
            "object_id": self.object_id,
            "confidence": self.confidence,
            "source_document": self.source_document,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_neo4j_properties(self) -> Dict[str, Any]:
        """
        转换为Neo4j关系属性
        
        Returns:
            dict: Neo4j关系属性字典
        """
        props = {
            "id": self.id,
            "subject": self.subject,
            "object": self.object,
            "relation": self.relation,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat() if self.created_at else datetime.now().isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else datetime.now().isoformat()
        }
        
        # 可选属性
        if self.subject_id:
            props["subject_id"] = self.subject_id
        if self.object_id:
            props["object_id"] = self.object_id
        if self.source_document:
            props["source_document"] = self.source_document
        if self.metadata:
            import json
            props["metadata"] = json.dumps(self.metadata, ensure_ascii=False)
            
        return props
    
    def get_neo4j_relationship_type(self) -> str:
        """
        获取Neo4j关系类型名称（大写下划线格式）
        
        Returns:
            str: Neo4j关系类型
        """
        # 将关系类型转换为Neo4j兼容的格式（大写，空格替换为下划线）
        return self.relation.upper().replace(" ", "_").replace("-", "_")
    
    def __eq__(self, other):
        """判断两个关系是否相等"""
        if not isinstance(other, Relation):
            return False
        return (self.subject == other.subject and 
                self.relation == other.relation and 
                self.object == other.object)
    
    def __hash__(self):
        """哈希函数"""
        return hash((self.subject, self.relation, self.object))
    
    def __repr__(self):
        return f"Relation('{self.subject}' --[{self.relation}]--> '{self.object}')"


class RelationCollection:
    """
    关系集合类
    
    用于批量处理关系
    """
    
    def __init__(self, relations: Optional[List[Relation]] = None):
        self._relations: List[Relation] = relations or []
    
    def add(self, relation: Relation):
        """添加关系"""
        self._relations.append(relation)
    
    def add_from_nlp_output(self, nlp_relations: List[Dict[str, Any]], source_document: Optional[str] = None):
        """从NLP输出批量添加关系"""
        for nlp_relation in nlp_relations:
            self._relations.append(Relation.from_nlp_output(nlp_relation, source_document))
    
    def get_by_type(self, relation_type: str) -> List[Relation]:
        """按类型筛选关系"""
        relation_type = relation_type.strip().lower()
        return [r for r in self._relations if r.relation == relation_type]
    
    def get_by_subject(self, subject: str) -> List[Relation]:
        """按主体筛选关系"""
        return [r for r in self._relations if r.subject == subject]
    
    def get_by_object(self, obj: str) -> List[Relation]:
        """按客体筛选关系"""
        return [r for r in self._relations if r.object == obj]
    
    def get_unique(self) -> List[Relation]:
        """获取去重后的关系列表"""
        seen = set()
        unique = []
        for relation in self._relations:
            key = (relation.subject, relation.relation, relation.object)
            if key not in seen:
                seen.add(key)
                unique.append(relation)
        return unique
    
    def get_all_relation_types(self) -> List[str]:
        """获取所有出现的关系类型"""
        return list(set(r.relation for r in self._relations))
    
    def to_list(self) -> List[Dict[str, Any]]:
        """转换为字典列表"""
        return [r.to_dict() for r in self._relations]
    
    def __iter__(self):
        return iter(self._relations)
    
    def __len__(self):
        return len(self._relations)
    
    def __getitem__(self, index):
        return self._relations[index]
