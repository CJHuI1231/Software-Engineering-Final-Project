import redis
import pickle
import time
import logging
from typing import Any, Dict, List, Optional, Callable
from functools import wraps

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CacheManager:
    """缓存管理器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化缓存管理器
        
        Args:
            config: 缓存配置
        """
        self.config = config or {}
        self.cache_type = self.config.get('type', 'memory')
        self.ttl = self.config.get('ttl', 3600)
        
        # 初始化缓存存储
        if self.cache_type == 'redis':
            self.redis_client = self._init_redis()
        else:
            self.memory_cache = {}
        
        logger.info(f"缓存管理器初始化完成，类型: {self.cache_type}")
    
    def _init_redis(self) -> redis.Redis:
        """初始化Redis客户端"""
        try:
            redis_config = self.config.get('redis', {})
            host = redis_config.get('host', 'localhost')
            port = redis_config.get('port', 6379)
            db = redis_config.get('db', 0)
            password = redis_config.get('password', None)
            
            client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True
            )
            
            # 测试连接
            client.ping()
            logger.info("Redis缓存连接成功")
            return client
            
        except Exception as e:
            logger.error(f"Redis缓存连接失败: {e}")
            raise RuntimeError(f"无法连接Redis缓存: {e}")
    
    def set_cache(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
            
        Returns:
            是否设置成功
        """
        try:
            ttl = ttl or self.ttl
            
            if self.cache_type == 'redis':
                # 使用pickle序列化值
                serialized_value = pickle.dumps(value)
                self.redis_client.setex(key, ttl, serialized_value)
            else:
                self.memory_cache[key] = {
                    'value': value,
                    'expire_time': time.time() + ttl
                }
            
            logger.debug(f"设置缓存: {key}, TTL: {ttl}")
            return True
            
        except Exception as e:
            logger.error(f"设置缓存失败: {e}")
            return False
    
    def get_cache(self, key: str) -> Any:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在或已过期则返回None
        """
        try:
            if self.cache_type == 'redis':
                # 获取并反序列化值
                serialized_value = self.redis_client.get(key)
                if serialized_value:
                    return pickle.loads(serialized_value)
                return None
            else:
                # 检查内存缓存
                cache_item = self.memory_cache.get(key)
                if cache_item:
                    # 检查是否过期
                    if time.time() < cache_item['expire_time']:
                        return cache_item['value']
                    else:
                        # 清理过期项
                        del self.memory_cache[key]
                        return None
                return None
                
        except Exception as e:
            logger.error(f"获取缓存失败: {e}")
            return None
    
    def delete_cache(self, key: str) -> bool:
        """
        删除缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        try:
            if self.cache_type == 'redis':
                self.redis_client.delete(key)
            else:
                if key in self.memory_cache:
                    del self.memory_cache[key]
            
            logger.debug(f"删除缓存: {key}")
            return True
            
        except Exception as e:
            logger.error(f"删除缓存失败: {e}")
            return False
    
    def clear_cache(self) -> bool:
        """
        清空所有缓存
        
        Returns:
            是否清空成功
        """
        try:
            if self.cache_type == 'redis':
                self.redis_client.flushdb()
            else:
                self.memory_cache.clear()
            
            logger.info("清空所有缓存")
            return True
            
        except Exception as e:
            logger.error(f"清空缓存失败: {e}")
            return False
    
    def cache_decorator(self, ttl: Optional[int] = None, key_prefix: str = "") -> Callable:
        """
        缓存装饰器
        
        Args:
            ttl: 过期时间（秒）
            key_prefix: 键前缀
            
        Returns:
            装饰器函数
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                # 生成缓存键
                cache_key = self._generate_cache_key(func.__name__, args, kwargs, key_prefix)
                
                # 尝试从缓存获取
                cached_result = self.get_cache(cache_key)
                if cached_result is not None:
                    logger.debug(f"从缓存获取结果: {cache_key}")
                    return cached_result
                
                # 执行函数
                result = func(*args, **kwargs)
                
                # 设置缓存
                self.set_cache(cache_key, result, ttl or self.ttl)
                
                return result
            
            return wrapper
        
        return decorator
    
    def _generate_cache_key(self, func_name: str, args: tuple, kwargs: dict, key_prefix: str = "") -> str:
        """
        生成缓存键
        
        Args:
            func_name: 函数名
            args: 函数参数
            kwargs: 函数关键字参数
            key_prefix: 键前缀
            
        Returns:
            缓存键
        """
        # 将参数转换为可哈希的字符串
        args_str = str(args) + str(kwargs)
        cache_key = f"{key_prefix}{func_name}:{args_str}"
        
        # 使用哈希函数生成固定长度的键
        import hashlib
        return hashlib.md5(cache_key.encode()).hexdigest()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        stats = {
            'type': self.cache_type,
            'ttl': self.ttl
        }
        
        if self.cache_type == 'redis':
            try:
                info = self.redis_client.info()
                stats.update({
                    'redis_version': info.get('redis_version', 'unknown'),
                    'connected_clients': info.get('connected_clients', 0),
                    'used_memory': info.get('used_memory', 0),
                    'total_commands': info.get('total_commands', 0)
                })
            except Exception as e:
                logger.error(f"获取Redis统计信息失败: {e}")
        else:
            stats.update({
                'cache_size': len(self.memory_cache),
                'cache_keys': list(self.memory_cache.keys())[:10]  # 只返回前10个键
            })
        
        return stats
    
    def is_cache_enabled(self) -> bool:
        """
        检查缓存是否启用
        
        Returns:
            是否启用缓存
        """
        return self.config.get('enabled', True)
    
    def set_cache_config(self, config: Dict[str, Any]) -> None:
        """
        设置缓存配置
        
        Args:
            config: 缓存配置
        """
        self.config = config
        self.cache_type = config.get('type', 'memory')
        self.ttl = config.get('ttl', 3600)
        
        # 重新初始化Redis客户端（如果需要）
        if self.cache_type == 'redis' and not hasattr(self, 'redis_client'):
            self.redis_client = self._init_redis()
        elif self.cache_type != 'redis':
            self.redis_client = None

class ModelCacheManager(CacheManager):
    """模型缓存管理器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化模型缓存管理器
        
        Args:
            config: 缓存配置
        """
        super().__init__(config)
        self.model_cache = {}
        logger.info("模型缓存管理器初始化完成")
    
    def cache_model(self, model_name: str, model: Any, ttl: Optional[int] = None) -> bool:
        """
        缓存模型
        
        Args:
            model_name: 模型名称
            model: 模型对象
            ttl: 过期时间（秒）
            
        Returns:
            是否缓存成功
        """
        try:
            self.model_cache[model_name] = {
                'model': model,
                'expire_time': time.time() + (ttl or self.ttl)
            }
            
            logger.debug(f"缓存模型: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"缓存模型失败: {e}")
            return False
    
    def get_model(self, model_name: str) -> Any:
        """
        获取缓存的模型
        
        Args:
            model_name: 模型名称
            
        Returns:
            模型对象，如果不存在或已过期则返回None
        """
        try:
            model_info = self.model_cache.get(model_name)
            if model_info:
                # 检查是否过期
                if time.time() < model_info['expire_time']:
                    return model_info['model']
                else:
                    # 清理过期模型
                    del self.model_cache[model_name]
                    return None
            return None
            
        except Exception as e:
            logger.error(f"获取模型失败: {e}")
            return None
    
    def clear_model_cache(self) -> bool:
        """
        清空模型缓存
        
        Returns:
            是否清空成功
        """
        try:
            self.model_cache.clear()
            logger.info("清空模型缓存")
            return True
            
        except Exception as e:
            logger.error(f"清空模型缓存失败: {e}")
            return False
    
    def get_model_cache_stats(self) -> Dict[str, Any]:
        """
        获取模型缓存统计信息
        
        Returns:
            模型缓存统计信息
        """
        return {
            'cache_size': len(self.model_cache),
            'cache_models': list(self.model_cache.keys()),
            'memory_usage': sum(len(str(model)) for model in self.model_cache.values())
        }

class BatchProcessingManager:
    """批量处理管理器"""
    
    def __init__(self, max_workers: int = 4, timeout: int = 30):
        """
        初始化批量处理管理器
        
        Args:
            max_workers: 最大工作线程数
            timeout: 超时时间（秒）
        """
        self.max_workers = max_workers
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        
        # 使用线程池
        from concurrent.futures import ThreadPoolExecutor
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.logger.info(f"批量处理管理器初始化完成，最大工作线程数: {max_workers}")
    
    def process_batch(self, items: List[Any], process_func: Callable, *args, **kwargs) -> List[Any]:
        """
        批量处理项目
        
        Args:
            items: 项目列表
            process_func: 处理函数
            args: 处理函数的位置参数
            kwargs: 处理函数的关键字参数
            
        Returns:
            处理结果列表
        """
        try:
            # 提交任务到线程池
            futures = []
            for item in items:
                future = self.executor.submit(process_func, item, *args, **kwargs)
                futures.append(future)
            
            # 等待结果
            results = []
            for future in futures:
                try:
                    result = future.result(timeout=self.timeout)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"批量处理单个项目失败: {e}")
                    results.append(None)
            
            return results
            
        except Exception as e:
            self.logger.error(f"批量处理失败: {e}")
            return []
    
    def shutdown(self) -> None:
        """关闭批量处理管理器"""
        try:
            self.executor.shutdown(wait=True)
            self.logger.info("批量处理管理器已关闭")
        except Exception as e:
            self.logger.error(f"关闭批量处理管理器失败: {e}")

def performance_monitor(func: Callable) -> Callable:
    """
    性能监控装饰器
    
    Args:
        func: 要监控的函数
        
    Returns:
        装饰后的函数
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        import time
        
        # 记录开始时间
        start_time = time.time()
        
        # 执行函数
        result = func(*args, **kwargs)
        
        # 计算执行时间
        execution_time = time.time() - start_time
        
        # 记录性能信息
        logger.info(f"函数 {func.__name__} 执行时间: {execution_time:.2f}秒")
        
        return result
    
    return wrapper

def memory_monitor(func: Callable) -> Callable:
    """
    内存监控装饰器
    
    Args:
        func: 要监控的函数
        
    Returns:
        装饰后的函数
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        import psutil
        import os
        
        # 获取进程信息
        process = psutil.Process(os.getpid())
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 执行函数
        result = func(*args, **kwargs)
        
        # 获取结束内存
        end_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 计算内存使用
        memory_usage = end_memory - start_memory
        
        # 记录内存信息
        logger.info(f"函数 {func.__name__} 内存使用: {memory_usage:.2f}MB")
        
        return result
    
    return wrapper

def async_processing(func: Callable) -> Callable:
    """
    异步处理装饰器
    
    Args:
        func: 要异步处理的函数
        
    Returns:
        装饰后的函数
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        import asyncio
        import threading
        
        # 创建事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 在新线程中运行异步函数
        def run_async():
            try:
                loop.run_until_complete(func(*args, **kwargs))
            except Exception as e:
                logger.error(f"异步处理失败: {e}")
            finally:
                loop.close()
        
        thread = threading.Thread(target=run_async)
        thread.start()
        thread.join(timeout=5)  # 设置超时
        
        return None
    
    return wrapper



