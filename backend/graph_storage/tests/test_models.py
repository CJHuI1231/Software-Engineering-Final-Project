"""
Graph Storage 单元测试

测试数据模型和基本功能
"""

import pytest
import json
from datetime import datetime

# 测试数据模型（不需要Neo4j连接）
from backend.graph_storage.models.entity_model import Entity, EntityType, EntityCollection
from backend.graph_storage.models.relation_model import Relation, RelationType, RelationCollection


class TestEntityModel:
    """实体模型测试"""
    
    def test_entity_creation(self):
        """测试实体创建"""
        entity = Entity(
            text="张三",
            type=EntityType.PERSON,
            confidence=0.95
        )
        
        assert entity.text == "张三"
        assert entity.type == EntityType.PERSON
        assert entity.confidence == 0.95
        assert entity.id is not None
    
    def test_entity_from_string_type(self):
        """测试从字符串类型创建实体"""
        entity = Entity(
            text="北京",
            type="GPE",
            confidence=0.8
        )
        
        assert entity.type == EntityType.GPE
    
    def test_entity_from_nlp_output(self):
        """测试从NLP输出创建实体"""
        nlp_output = {
            "text": "阿里巴巴",
            "type": "ORG",
            "start_pos": 10,
            "end_pos": 14,
            "confidence": 0.92
        }
        
        entity = Entity.from_nlp_output(nlp_output, source_document="test.pdf")
        
        assert entity.text == "阿里巴巴"
        assert entity.type == EntityType.ORG
        assert entity.start_pos == 10
        assert entity.end_pos == 14
        assert entity.confidence == 0.92
        assert entity.source_document == "test.pdf"
    
    def test_entity_to_dict(self):
        """测试实体转字典"""
        entity = Entity(
            text="李四",
            type=EntityType.PERSON,
            confidence=0.88
        )
        
        data = entity.to_dict()
        
        assert data["text"] == "李四"
        assert data["type"] == "PERSON"
        assert data["confidence"] == 0.88
        assert "id" in data
    
    def test_entity_to_neo4j_properties(self):
        """测试实体转Neo4j属性"""
        entity = Entity(
            text="深圳",
            type=EntityType.GPE,
            confidence=0.9,
            metadata={"country": "China"}
        )
        
        props = entity.to_neo4j_properties()
        
        assert props["text"] == "深圳"
        assert props["type"] == "GPE"
        assert "metadata" in props
        assert json.loads(props["metadata"])["country"] == "China"
    
    def test_entity_type_from_string(self):
        """测试实体类型字符串转换"""
        assert EntityType.from_string("PERSON") == EntityType.PERSON
        assert EntityType.from_string("person") == EntityType.PERSON
        assert EntityType.from_string("invalid") == EntityType.UNKNOWN
    
    def test_entity_equality(self):
        """测试实体相等性"""
        e1 = Entity(text="张三", type=EntityType.PERSON)
        e2 = Entity(text="张三", type=EntityType.PERSON)
        e3 = Entity(text="李四", type=EntityType.PERSON)
        
        assert e1 == e2
        assert e1 != e3
    
    def test_confidence_bounds(self):
        """测试置信度边界"""
        entity1 = Entity(text="test", type=EntityType.UNKNOWN, confidence=1.5)
        entity2 = Entity(text="test", type=EntityType.UNKNOWN, confidence=-0.5)
        
        assert entity1.confidence == 1.0
        assert entity2.confidence == 0.0


class TestEntityCollection:
    """实体集合测试"""
    
    def test_collection_creation(self):
        """测试集合创建"""
        collection = EntityCollection()
        assert len(collection) == 0
    
    def test_collection_add(self):
        """测试添加实体"""
        collection = EntityCollection()
        entity = Entity(text="测试", type=EntityType.UNKNOWN)
        collection.add(entity)
        
        assert len(collection) == 1
    
    def test_collection_from_nlp_output(self):
        """测试从NLP输出批量添加"""
        collection = EntityCollection()
        nlp_entities = [
            {"text": "张三", "type": "PERSON"},
            {"text": "北京", "type": "GPE"}
        ]
        
        collection.add_from_nlp_output(nlp_entities)
        
        assert len(collection) == 2
    
    def test_collection_get_by_type(self):
        """测试按类型筛选"""
        collection = EntityCollection()
        collection.add(Entity(text="张三", type=EntityType.PERSON))
        collection.add(Entity(text="北京", type=EntityType.GPE))
        collection.add(Entity(text="李四", type=EntityType.PERSON))
        
        persons = collection.get_by_type(EntityType.PERSON)
        
        assert len(persons) == 2
    
    def test_collection_get_unique(self):
        """测试去重"""
        collection = EntityCollection()
        collection.add(Entity(text="张三", type=EntityType.PERSON))
        collection.add(Entity(text="张三", type=EntityType.PERSON))
        collection.add(Entity(text="李四", type=EntityType.PERSON))
        
        unique = collection.get_unique()
        
        assert len(unique) == 2


class TestRelationModel:
    """关系模型测试"""
    
    def test_relation_creation(self):
        """测试关系创建"""
        relation = Relation(
            subject="张三",
            relation=RelationType.WORKS_AT,
            object="阿里巴巴",
            confidence=0.85
        )
        
        assert relation.subject == "张三"
        assert relation.relation == RelationType.WORKS_AT
        assert relation.object == "阿里巴巴"
        assert relation.confidence == 0.85
    
    def test_relation_from_string_type(self):
        """测试从字符串类型创建关系"""
        relation = Relation(
            subject="张三",
            relation="works_at",
            object="公司"
        )
        
        assert relation.relation == RelationType.WORKS_AT
    
    def test_relation_from_nlp_output(self):
        """测试从NLP输出创建关系"""
        nlp_output = {
            "subject": "张三",
            "relation": "lives_in",
            "object": "北京",
            "confidence": 0.9
        }
        
        relation = Relation.from_nlp_output(nlp_output, source_document="test.pdf")
        
        assert relation.subject == "张三"
        assert relation.relation == RelationType.LIVES_IN
        assert relation.object == "北京"
        assert relation.source_document == "test.pdf"
    
    def test_relation_to_dict(self):
        """测试关系转字典"""
        relation = Relation(
            subject="公司A",
            relation=RelationType.PART_OF,
            object="集团B"
        )
        
        data = relation.to_dict()
        
        assert data["subject"] == "公司A"
        assert data["relation"] == "part_of"
        assert data["object"] == "集团B"
    
    def test_relation_neo4j_type(self):
        """测试Neo4j关系类型名称"""
        relation = Relation(
            subject="A",
            relation=RelationType.WORKS_AT,
            object="B"
        )
        
        assert relation.get_neo4j_relationship_type() == "WORKS_AT"
    
    def test_relation_type_from_string(self):
        """测试关系类型字符串转换"""
        assert RelationType.from_string("works_at") == RelationType.WORKS_AT
        assert RelationType.from_string("WORKS_AT") == RelationType.WORKS_AT
        assert RelationType.from_string("invalid") == RelationType.UNKNOWN


class TestRelationCollection:
    """关系集合测试"""
    
    def test_collection_creation(self):
        """测试集合创建"""
        collection = RelationCollection()
        assert len(collection) == 0
    
    def test_collection_get_by_subject(self):
        """测试按主体筛选"""
        collection = RelationCollection()
        collection.add(Relation(subject="张三", relation=RelationType.WORKS_AT, object="公司A"))
        collection.add(Relation(subject="张三", relation=RelationType.LIVES_IN, object="北京"))
        collection.add(Relation(subject="李四", relation=RelationType.WORKS_AT, object="公司B"))
        
        relations = collection.get_by_subject("张三")
        
        assert len(relations) == 2
    
    def test_collection_get_by_type(self):
        """测试按类型筛选"""
        collection = RelationCollection()
        collection.add(Relation(subject="张三", relation=RelationType.WORKS_AT, object="公司A"))
        collection.add(Relation(subject="李四", relation=RelationType.WORKS_AT, object="公司B"))
        collection.add(Relation(subject="王五", relation=RelationType.LIVES_IN, object="上海"))
        
        works_at = collection.get_by_type(RelationType.WORKS_AT)
        
        assert len(works_at) == 2


class TestConfigAndErrors:
    """配置和错误处理测试"""
    
    def test_default_config(self):
        """测试默认配置"""
        from backend.graph_storage.utils.config import get_default_config
        
        config = get_default_config()
        
        assert config.neo4j.uri == "bolt://localhost:7687"
        assert config.neo4j.user == "neo4j"
    
    def test_config_to_dict(self):
        """测试配置转字典"""
        from backend.graph_storage.utils.config import GraphConfig
        
        config = GraphConfig()
        data = config.to_dict()
        
        assert "neo4j" in data
        assert data["neo4j"]["uri"] == "bolt://localhost:7687"
    
    def test_error_classes(self):
        """测试错误类"""
        from backend.graph_storage.utils.errors import (
            GraphStorageError,
            EntityNotFoundError,
            RelationNotFoundError,
            ValidationError
        )
        
        # 基础错误
        error = GraphStorageError("Test error", code="TEST")
        assert error.message == "Test error"
        assert error.code == "TEST"
        
        # 实体未找到
        entity_error = EntityNotFoundError("entity-123")
        assert "entity-123" in entity_error.message
        
        # 关系未找到
        relation_error = RelationNotFoundError("rel-456")
        assert "rel-456" in relation_error.message
        
        # 验证错误
        validation_error = ValidationError("Invalid input", field="text")
        assert validation_error.field == "text"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
