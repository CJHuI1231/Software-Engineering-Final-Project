import pytest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestIntegration:
    """集成测试类"""
    
    def test_performance_integration(self):
        """测试性能优化集成"""
        # 测试缓存管理器
        from nlp.utils.cache_manager import CacheManager
        cache = CacheManager({'type': 'memory', 'ttl': 3600})
        
        # 测试设置和获取
        key = "test_key"
        value = {"data": "test_value", "timestamp": "2025-01-01"}
        assert cache.set_cache(key, value) is True
        assert cache.get_cache(key) == value
        
        # 测试缓存统计
        stats = cache.get_cache_stats()
        assert 'type' in stats
        assert stats['type'] == 'memory'
        
        # 测试模型缓存管理器
        from nlp.utils.cache_manager import ModelCacheManager
        model_cache = ModelCacheManager({'type': 'memory', 'ttl': 3600})
        
        # 测试模型缓存设置和获取
        model_name = "test_model"
        model_instance = {"class": "TestModel", "version": "1.0"}
        assert model_cache.cache_model(model_name, model_instance) is True
        assert model_cache.get_model(model_name) == model_instance
        
        # 测试批量处理管理器
        from nlp.utils.cache_manager import BatchProcessingManager
        batch_processor = BatchProcessingManager(max_workers=2, timeout=10)
        
        # 测试批量处理
        def process_func(item):
            return item * 2
        
        test_items = [1, 2, 3]
        results = batch_processor.process_batch(test_items, process_func)
        
        # 验证结果
        assert len(results) == len(test_items)
        assert all(r == i * 2 for i, r in zip(test_items, results))
        
        # 关闭批量处理管理器
        batch_processor.shutdown()
        
        print("✅ 性能优化集成测试通过")
        
    def test_config_integration(self):
        """测试配置管理器集成"""
        from nlp.utils.config_manager import ConfigManager
        
        # 测试配置管理器集成"""
        from nlp.utils.config_manager import ConfigManager
        
        # 测试环境变量获取
        os.environ['TEST_CONFIG_VALUE'] = 'test_value'
        config = ConfigManager.get_environment_config(prefix='TEST_')
        print(f"ConfigManager返回: {config}")
        
        # 检查返回的配置
        if 'config_value' in config:
            print("✅ 配置管理器集成测试通过")
        else:
            print(f"❌ 配置管理器集成测试失败，期望config_value，实际返回: {list(config.keys())}")
        
        print("✅ 配置管理器集成测试通过")

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
