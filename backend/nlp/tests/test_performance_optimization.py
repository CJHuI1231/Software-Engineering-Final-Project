import pytest
import sys
import os
import time

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nlp.entity_recognition.entity_recognition import EntityRecognitionModel
from nlp.summary.summary_model import SummaryModel
from nlp.utils.cache_manager import CacheManager, ModelCacheManager

class TestPerformanceOptimization:
    """性能优化测试类"""
    
    @pytest.fixture
    def cache_config(self):
        """创建缓存配置"""
        return {
            'type': 'memory',
            'ttl': 3600
        }
    
    @pytest.fixture
    def entity_model(self, cache_config):
        """创建实体识别模型实例"""
        return EntityRecognitionModel(cache_config)
    
    @pytest.fixture
    def summary_model(self, cache_config):
        """创建摘要模型实例"""
        return SummaryModel(cache_config)
    
    def test_entity_recognition_cache(self, entity_model):
        """测试实体识别的缓存功能"""
        # 测试文本
        test_text = "张三在阿里巴巴工作，李四在腾讯上班。"
        
        # 第一次调用（无缓存）
        start_time = time.time()
        entities1 = entity_model.recognize_entities(test_text)
        first_call_time = time.time() - start_time
        
        # 第二次调用（有缓存）
        start_time = time.time()
        entities2 = entity_model.recognize_entities(test_text)
        second_call_time = time.time() - start_time
        
        # 验证结果一致性
        assert entities1 == entities2
        assert len(entities1) > 0
        
        # 验证缓存效果（第二次调用应该更快）
        assert second_call_time < first_call_time
        
        print(f"首次调用时间: {first_call_time:.4f}秒")
        print(f"缓存调用时间: {second_call_time:.4f}秒")
        print(f"性能提升: {(first_call_time - second_call_time) / first_call_time * 100:.1f}%")
    
    def test_summary_cache(self, summary_model):
        """测试摘要生成的缓存功能"""
        # 测试文本
        test_text = "这是一段很长的测试文本，用于测试摘要生成功能的性能。" * 10
        
        # 第一次调用（无缓存）
        start_time = time.time()
        summary1 = summary_model.generate_bart_summary(test_text)
        first_call_time = time.time() - start_time
        
        # 第二次调用（有缓存）
        start_time = time.time()
        summary2 = summary_model.generate_bart_summary(test_text)
        second_call_time = time.time() - start_time
        
        # 验证结果一致性
        assert summary1 == summary2
        assert len(summary1) > 0
        
        # 验证缓存效果（第二次调用应该更快）
        assert second_call_time < first_call_time
        
        print(f"摘要首次调用时间: {first_call_time:.4f}秒")
        print(f"摘要缓存调用时间: {second_call_time:.4f}秒")
        print(f"性能提升: {(first_call_time - second_call_time) / first_call_time * 100:.1f}%")
    
    def test_entity_batch_processing(self, entity_model):
        """测试实体识别的批量处理功能"""
        # 测试文本列表
        test_texts = [
            "张三在阿里巴巴工作。",
            "李四在腾讯上班。",
            "王五在百度实习。",
            "赵六在字节跳动。",
            "钱七在华为工作。"
        ]
        
        # 测试批量处理
        start_time = time.time()
        batch_results = entity_model.batch_process(test_texts, "entity_recognition")
        batch_time = time.time() - start_time
        
        # 测试单个处理
        start_time = time.time()
        individual_results = []
        for text in test_texts:
            result = entity_model.analyze_text_with_llm(text, "entity_recognition")
            individual_results.append(result)
        individual_time = time.time() - start_time
        
        # 验证结果数量
        assert len(batch_results) == len(test_texts)
        assert len(individual_results) == len(test_texts)
        
        # 验证每个结果都有实体
        for result in batch_results:
            assert "entities" in result
            assert isinstance(result["entities"], list)
        
        # 验证批量处理性能（应该更快或至少不慢太多）
        print(f"批量处理时间: {batch_time:.4f}秒")
        print(f"单独处理时间: {individual_time:.4f}秒")
        print(f"性能提升: {(individual_time - batch_time) / individual_time * 100:.1f}%")
    
    def test_summary_batch_processing(self, summary_model):
        """测试摘要生成的批量处理功能"""
        # 测试文本列表
        test_texts = [
            "这是一段很长的测试文本，用于测试摘要生成功能的性能。" * 10,
            "这是另一段很长的测试文本，内容有所不同，但同样用于测试性能。" * 10,
            "第三段测试文本，同样很长，用于测试批量处理功能的效果。" * 10,
            "第四段测试文本，继续验证批量处理功能的性能优势。" * 10,
            "最后一段测试文本，用于完成批量处理功能的性能测试。" * 10
        ]
        
        # 测试批量处理
        start_time = time.time()
        batch_results = summary_model.batch_generate_summaries(test_texts, "bart")
        batch_time = time.time() - start_time
        
        # 测试单个处理
        start_time = time.time()
        individual_results = []
        for text in test_texts:
            result = summary_model.generate_bart_summary(text)
            individual_results.append({
                "original_text": text,
                "summary": result,
                "method_used": "bart",
                "summary_length": len(result)
            })
        individual_time = time.time() - start_time
        
        # 验证结果数量
        assert len(batch_results) == len(test_texts)
        assert len(individual_results) == len(test_texts)
        
        # 验证每个结果都有摘要
        for result in batch_results:
            assert "summary" in result
            assert len(result["summary"]) > 0
        
        # 验证批量处理性能（应该更快或至少不慢太多）
        print(f"摘要批量处理时间: {batch_time:.4f}秒")
        print(f"摘要单独处理时间: {individual_time:.4f}秒")
        print(f"性能提升: {(individual_time - batch_time) / individual_time * 100:.1f}%")
    
    def test_model_caching(self, cache_config):
        """测试模型缓存功能"""
        # 创建两个模型实例
        model1 = EntityRecognitionModel(cache_config)
        model2 = EntityRecognitionModel(cache_config)
        
        # 验证模型缓存功能
        # 由于模型缓存是静态的，两个实例应该使用同一个缓存
        # 这个测试主要验证模型缓存不会引起异常
        
        # 测试第一个模型
        text = "张三在阿里巴巴工作。"
        entities1 = model1.recognize_entities(text)
        assert len(entities1) > 0
        
        # 测试第二个模型
        entities2 = model2.recognize_entities(text)
        assert len(entities2) > 0
        
        # 验证结果一致性
        assert entities1 == entities2
        
        print("模型缓存功能正常工作")
    
    def test_cache_manager(self):
        """测试缓存管理器"""
        # 创建缓存管理器
        cache = CacheManager({
            'type': 'memory',
            'ttl': 3600
        })
        
        # 测试缓存设置
        key = "test_key"
        value = {"data": "test_value", "timestamp": time.time()}
        result = cache.set_cache(key, value)
        assert result is True
        
        # 测试缓存获取
        cached_value = cache.get_cache(key)
        assert cached_value == value
        
        # 测试缓存统计
        stats = cache.get_cache_stats()
        assert 'type' in stats
        assert 'cache_size' in stats
        assert stats['type'] == 'memory'
        
        print("缓存管理器功能正常")
    
    def test_model_cache_manager(self):
        """测试模型缓存管理器"""
        # 创建模型缓存管理器
        model_cache = ModelCacheManager({
            'type': 'memory',
            'ttl': 3600
        })
        
        # 测试模型缓存设置
        model_name = "test_model"
        model_instance = {"class": "TestModel", "version": "1.0"}
        result = model_cache.cache_model(model_name, model_instance)
        assert result is True
        
        # 测试模型缓存获取
        cached_model = model_cache.get_model(model_name)
        assert cached_model == model_instance
        
        # 测试缓存统计
        stats = model_cache.get_model_cache_stats()
        assert 'cache_size' in stats
        assert 'cache_models' in stats
        assert stats['cache_size'] >= 1
        
        print("模型缓存管理器功能正常")

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__])



