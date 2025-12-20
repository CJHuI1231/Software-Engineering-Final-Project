import pytest
import sys
import os
import time
import typing

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestPerformanceSimple:
    """简化的性能测试类"""
    
    def test_cache_manager(self):
        """测试缓存管理器"""
        # 导入缓存管理器
        from nlp.utils.cache_manager import CacheManager
        
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
        # 导入模型缓存管理器
        from nlp.utils.cache_manager import ModelCacheManager
        
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
    
    def test_performance_monitor_decorator(self):
        """测试性能监控装饰器"""
        # 导入性能监控装饰器
        from nlp.utils.cache_manager import performance_monitor
        
        # 创建测试函数
        @performance_monitor
        def test_function():
            time.sleep(0.1)  # 模拟耗时操作
            return "test_result"
        
        # 执行测试函数
        result = test_function()
        
        # 验证结果
        assert result == "test_result"
        
        print("性能监控装饰器功能正常")
    
    def test_memory_monitor_decorator(self):
        """测试内存监控装饰器"""
        # 导入内存监控装饰器
        from nlp.utils.cache_manager import memory_monitor
        
        # 创建测试函数
        @memory_monitor
        def test_function():
            # 创建一些对象以使用内存
            test_list = [i for i in range(1000)]
            return test_list
        
        # 执行测试函数
        result = test_function()
        
        # 验证结果
        assert len(result) == 1000
        
        print("内存监控装饰器功能正常")
    
    def test_batch_processing_manager(self):
        """测试批量处理管理器"""
        # 导入批量处理管理器
        from nlp.utils.cache_manager import BatchProcessingManager
        
        # 创建批量处理管理器
        batch_processor = BatchProcessingManager(max_workers=2, timeout=10)
        
        # 创建处理函数
        def process_func(item):
            return item * 2
        
        # 创建测试数据
        test_items = [1, 2, 3, 4, 5]
        
        # 执行批量处理
        results = batch_processor.process_batch(test_items, process_func)
        
        # 验证结果
        assert len(results) == len(test_items)
        assert all(r == i * 2 for i, r in zip(test_items, results))
        
        # 关闭批量处理管理器
        batch_processor.shutdown()
        
        print("批量处理管理器功能正常")
    
    def test_config_manager(self):
        """测试配置管理器"""
        # 导入配置管理器
        from nlp.utils.config_manager import ConfigManager
        
        # 测试配置加载
        config = ConfigManager.get_environment_config(prefix="TEST_")
        assert isinstance(config, dict)
        
        print("配置管理器功能正常")

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
