import pytest
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nlp.entity_recognition.entity_recognition import EntityRecognitionModel

class TestEntityRecognition:
    """实体识别模块测试类"""
    
    @pytest.fixture
    def entity_model(self):
        """创建实体识别模型实例"""
        return EntityRecognitionModel()
    
    def test_recognize_entities(self, entity_model):
        """测试实体识别功能"""
        # 测试文本
        test_text = "张三在阿里巴巴工作，李四在腾讯上班。"
        
        # 执行实体识别
        entities = entity_model.recognize_entities(test_text)
        
        # 验证结果
        assert isinstance(entities, list)
        assert len(entities) > 0
        
        # 验证实体格式
        for entity in entities:
            assert "text" in entity
            assert "type" in entity
            assert "start_pos" in entity
            assert "end_pos" in entity
            assert "confidence" in entity
        
        # 验证特定实体
        person_entities = [e for e in entities if e["type"] == "PERSON"]
        organization_entities = [e for e in entities if e["type"] == "ORG"]
        
        assert len(person_entities) >= 2  # 张三和李四
        assert len(organization_entities) >= 2  # 阿里巴巴和腾讯
    
    def test_recognize_entities_with_transformers(self, entity_model):
        """测试使用transformers的实体识别功能"""
        # 测试文本
        test_text = "张三在阿里巴巴工作，李四在腾讯上班。"
        
        # 执行实体识别
        entities = entity_model.recognize_entities_with_transformers(test_text)
        
        # 验证结果
        assert isinstance(entities, list)
        assert len(entities) > 0
        
        # 验证实体格式
        for entity in entities:
            assert "text" in entity
            assert "type" in entity
            assert "start_pos" in entity
            assert "end_pos" in entity
            assert "confidence" in entity
    
    def test_classify_entities(self, entity_model):
        """测试实体分类功能"""
        # 测试实体列表
        test_entities = [
            {"text": "张三", "type": "PERSON", "start_pos": 0, "end_pos": 2, "confidence": 0.95},
            {"text": "阿里巴巴", "type": "ORG", "start_pos": 3, "end_pos": 7, "confidence": 0.90},
            {"text": "李四", "type": "PERSON", "start_pos": 8, "end_pos": 10, "confidence": 0.92},
            {"text": "腾讯", "type": "ORG", "start_pos": 11, "end_pos": 13, "confidence": 0.88}
        ]
        
        # 执行实体分类
        classified_entities = entity_model.classify_entities(test_entities)
        
        # 验证结果
        assert isinstance(classified_entities, dict)
        assert "PERSON" in classified_entities
        assert "ORG" in classified_entities
        
        # 验证分类结果
        person_entities = classified_entities["PERSON"]
        org_entities = classified_entities["ORG"]
        
        assert len(person_entities) == 2  # 张三和李四
        assert len(org_entities) == 2  # 阿里巴巴和腾讯
    
    def test_extract_entity_relations(self, entity_model):
        """测试实体关系提取功能"""
        # 测试文本
        test_text = "张三在阿里巴巴工作，李四在腾讯上班。"
        
        # 执行实体关系提取
        relations = entity_model.extract_entity_relations(test_text)
        
        # 验证结果
        assert isinstance(relations, list)
        assert len(relations) > 0
        
        # 验证关系格式
        for relation in relations:
            assert "subject" in relation
            assert "relation" in relation
            assert "object" in relation
    
    def test_analyze_text_with_llm(self, entity_model):
        """测试LLM文本分析功能"""
        # 测试文本
        test_text = "张三在阿里巴巴工作，李四在腾讯上班。"
        
        # 执行LLM分析
        result = entity_model.analyze_text_with_llm(test_text, "entity_recognition")
        
        # 验证结果
        assert isinstance(result, dict)
        assert "status" in result
        assert result["status"] == "success"
        assert "entities" in result
    
    def test_get_supported_entity_types(self, entity_model):
        """测试获取支持的实体类型功能"""
        # 获取支持的实体类型
        entity_types = entity_model.get_supported_entity_types()
        
        # 验证结果
        assert isinstance(entity_types, list)
        assert len(entity_types) > 0
        assert "PERSON" in entity_types
        assert "ORG" in entity_types
        assert "DATE" in entity_types
        assert "LOCATION" in entity_types
    
    def test_batch_process(self, entity_model):
        """测试批量处理功能"""
        # 测试文本列表
        test_texts = [
            "张三在阿里巴巴工作。",
            "李四在腾讯上班。",
            "王五在百度实习。"
        ]
        
        # 执行批量处理
        results = entity_model.batch_process(test_texts, "entity_recognition")
        
        # 验证结果
        assert isinstance(results, list)
        assert len(results) == len(test_texts)
        
        # 验证每个结果
        for result in results:
            assert isinstance(result, dict)
            assert "status" in result
            assert result["status"] == "success"
            assert "entities" in result
    
    def test_empty_text_handling(self, entity_model):
        """测试空文本处理"""
        # 测试空文本
        empty_text = ""
        entities = entity_model.recognize_entities(empty_text)
        
        # 验证结果
        assert isinstance(entities, list)
        assert len(entities) == 0
    
    def test_none_text_handling(self, entity_model):
        """测试None文本处理"""
        # 测试None文本
        entities = entity_model.recognize_entities(None)
        
        # 验证结果
        assert isinstance(entities, list)
        assert len(entities) == 0
    
    def test_invalid_input_handling(self, entity_model):
        """测试无效输入处理"""
        # 测试非字符串输入
        invalid_input = 12345
        entities = entity_model.recognize_entities(invalid_input)
        
        # 验证结果
        assert isinstance(entities, list)
        assert len(entities) == 0

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__])



