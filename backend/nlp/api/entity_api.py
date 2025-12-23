from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from nlp.entity_recognition.entity_recognition import EntityRecognitionModel
from nlp.utils.cache_manager import (
    CacheManager,
    performance_monitor,
    memory_monitor
)
from nlp.utils.config_manager import ConfigManager
import logging
import time
from typing import List, Dict, Any

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建API路由器
router = APIRouter(
    prefix="/api/nlp/entities",
    tags=["Entity Recognition"]
)

# 添加CORS中间件到主应用（不在子路由中添加）
# 注意：CORS中间件需要在主应用的FastAPI实例上配置

# 初始化实体识别模型
# 加载配置
config = ConfigManager.get_environment_config(prefix="NLP_") or {}

# 初始化实体识别模型（不传参数）
try:
    entity_model = EntityRecognitionModel()
    logger.info("实体识别模型初始化成功")
except Exception as e:
    logger.error(f"实体识别模型初始化失败: {e}")
    entity_model = None

# 初始化API缓存
try:
    cache_config = config.get('cache', {
        'type': 'memory',
        'ttl': 3600
    })
    api_cache = CacheManager(cache_config)
    logger.info("缓存管理器初始化成功")
except Exception as e:
    logger.error(f"缓存管理器初始化失败: {e}")
    api_cache = None

logger.info("实体识别API初始化完成")

@router.post("/")
@performance_monitor
@memory_monitor
def recognize_entities(request: Dict[str, Any]):
    """
    识别文本中的实体
    
    请求格式:
    {
        "text": "需要识别实体的文本",
        "entity_types": ["PERSON", "ORG", "DATE", "LOCATION"],
        "relation_extraction": true
    }
    
    响应格式:
    {
        "status": "success",
        "entities": [
            {
                "text": "张三",
                "type": "PERSON",
                "start_pos": 0,
                "end_pos": 2,
                "confidence": 0.95
            }
        ],
        "relations": [
            {
                "subject": "张三",
                "relation": "works_at",
                "object": "阿里巴巴"
            }
        ],
        "processing_time": 1.2
    }
    """
    try:
        # 检查模型是否初始化
        if not entity_model:
            raise HTTPException(status_code=503, detail="实体识别服务暂时不可用")
        
        # 获取请求参数
        text = request.get('text', '')
        entity_types = request.get('entity_types', [])
        relation_extraction = request.get('relation_extraction', False)
        
        if not text:
            raise HTTPException(status_code=400, detail="文本内容不能为空")
        
        # 尝试从缓存获取结果
        cache_key = f"api_entities_{hash(text)}_{str(entity_types)}_{relation_extraction}"
        if api_cache:
            cached_result = api_cache.get_cache(cache_key)
            if cached_result is not None:
                logger.info("从API缓存获取实体识别结果")
                return cached_result
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 执行实体识别
        entities = entity_model.recognize_entities(text)
        
        # 如果需要提取关系
        relations = []
        if relation_extraction:
            relations = entity_model.extract_entity_relations(text)
        
        # 计算处理时间
        processing_time = time.time() - start_time
        
        # 构建响应
        response = {
            "status": "success",
            "entities": entities,
            "relations": relations,
            "processing_time": round(processing_time, 2),
            "entity_types_supported": entity_model.get_supported_entity_types()
        }
        
        # 缓存结果
        if api_cache:
            api_cache.set_cache(cache_key, response, ttl=1800)  # 缓存30分钟
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"实体识别API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch")
@performance_monitor
@memory_monitor
def batch_recognize_entities(request: Dict[str, Any]):
    """
    批量识别文本中的实体
    
    请求格式:
    {
        "texts": ["文本1", "文本2", "文本3"],
        "entity_types": ["PERSON", "ORG"],
        "relation_extraction": false
    }
    
    响应格式:
    {
        "status": "success",
        "results": [
            {
                "text": "文本1",
                "entities": [...],
                "relations": [...],
                "processing_time": 0.5
            }
        ]
    }
    """
    try:
        # 检查模型是否初始化
        if not entity_model:
            raise HTTPException(status_code=503, detail="实体识别服务暂时不可用")
        
        # 获取请求参数
        texts = request.get('texts', [])
        entity_types = request.get('entity_types', [])
        relation_extraction = request.get('relation_extraction', False)
        
        if not texts or not isinstance(texts, list):
            raise HTTPException(status_code=400, detail="文本列表不能为空")
        
        # 尝试从缓存获取结果
        cache_key = f"api_batch_entities_{hash(str(texts))}_{str(entity_types)}_{relation_extraction}"
        if api_cache:
            cached_result = api_cache.get_cache(cache_key)
            if cached_result is not None:
                logger.info("从API缓存获取批量实体识别结果")
                return cached_result
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 使用模型批量处理功能
        task = "entity_recognition"
        if relation_extraction:
            # 如果需要关系提取，先进行实体识别，然后进行关系提取
            results = []
            for text in texts:
                # 执行实体识别
                entities = entity_model.recognize_entities(text)
                
                # 如果需要提取关系
                relations = []
                if relation_extraction:
                    relations = entity_model.extract_entity_relations(text)
                
                results.append({
                    "text": text,
                    "entities": entities,
                    "relations": relations,
                    "processing_time": 0.0  # 实际应用中应该记录每个文本的处理时间
                })
        else:
            # 如果不需要关系提取，使用批量处理
            batch_results = entity_model.batch_process(texts, task)
            results = []
            for i, text in enumerate(texts):
                entities = batch_results[i] if i < len(batch_results) else []
                results.append({
                    "text": text,
                    "entities": entities,
                    "relations": [],
                    "processing_time": 0.0
                })
        
        # 计算总处理时间
        processing_time = time.time() - start_time
        
        # 构建响应
        response = {
            "status": "success",
            "results": results,
            "total_processing_time": round(processing_time, 2),
            "entity_types_supported": entity_model.get_supported_entity_types()
        }
        
        # 缓存结果
        if api_cache:
            api_cache.set_cache(cache_key, response, ttl=1800)  # 缓存30分钟
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量实体识别API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/classify")
def classify_entities(request: Dict[str, Any]):
    """
    对实体进行分类
    
    请求格式:
    {
        "entities": [
            {"text": "张三", "type": "PERSON", "start_pos": 0, "end_pos": 2, "confidence": 0.95}
        ]
    }
    
    响应格式:
    {
        "status": "success",
        "classified_entities": {
            "PERSON": [
                {"text": "张三", "type": "PERSON", "start_pos": 0, "end_pos": 2, "confidence": 0.95}
            ]
        }
    }
    """
    try:
        # 获取请求参数
        entities = request.get('entities', [])
        
        if not entities or not isinstance(entities, list):
            raise HTTPException(status_code=400, detail="实体列表不能为空")
        
        # 执行实体分类
        classified_entities = entity_model.classify_entities(entities)
        
        # 构建响应
        return {
            "status": "success",
            "classified_entities": classified_entities,
            "entity_types_supported": entity_model.get_supported_entity_types()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"实体分类API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/llm")
def analyze_with_llm(request: Dict[str, Any]):
    """
    使用LLM进行文本分析
    
    请求格式:
    {
        "text": "需要分析的文本",
        "task": "entity_recognition|summary"
    }
    
    响应格式:
    {
        "status": "success",
        "result": {...},
        "method_used": "transformers_ner"
    }
    """
    try:
        # 获取请求参数
        text = request.get('text', '')
        task = request.get('task', 'entity_recognition')
        
        if not text:
            raise HTTPException(status_code=400, detail="文本内容不能为空")
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 使用LLM进行分析
        result = entity_model.analyze_text_with_llm(text, task)
        
        # 计算处理时间
        processing_time = time.time() - start_time
        
        # 构建响应
        return {
            "status": "success",
            "result": result,
            "processing_time": round(processing_time, 2),
            "task": task
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LLM分析API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/info")
def get_entity_info():
    """
    获取实体识别相关信息
    
    响应格式:
    {
        "status": "success",
        "supported_entity_types": ["PERSON", "ORG", "DATE", "LOCATION"],
        "model_info": {
            "name": "spaCy + transformers",
            "version": "1.0.0",
            "description": "基于spaCy和transformers的实体识别模型"
        }
    }
    """
    try:
        # 获取支持的实体类型
        supported_types = entity_model.get_supported_entity_types()
        
        # 构建响应
        return {
            "status": "success",
            "supported_entity_types": supported_types,
            "model_info": {
                "name": "spaCy + transformers",
                "version": "1.0.0",
                "description": "基于spaCy和transformers的实体识别模型"
            }
        }
        
    except Exception as e:
        logger.error(f"获取实体信息API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 导出 APIRouter 供主应用使用
__all__ = ["router"]