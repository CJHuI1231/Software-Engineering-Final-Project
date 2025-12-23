from fastapi import APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from nlp.summary.summary_model import SummaryModel
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

router = APIRouter(
    prefix="/api/nlp/summary",
    tags=["Summary"]
)

# 注意：CORS中间件需要在主应用的FastAPI实例上配置，不在子路由中添加

# 初始化摘要模型
# 加载配置
config = ConfigManager.get_environment_config(prefix="NLP_") or {}

# 初始化摘要模型
try:
    summary_model = SummaryModel(config)
    logger.info("摘要模型初始化成功")
except Exception as e:
    logger.error(f"摘要模型初始化失败: {e}")
    summary_model = None

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

logger.info("摘要API初始化完成")

@router.post("/")
@performance_monitor
@memory_monitor
def generate_summary(request: Dict[str, Any]):
    """
    生成文本摘要
    
    请求格式:
    {
        "text": "需要生成摘要的文本",
        "method": "bart|textrank|auto",
        "max_length": 150,
        "min_length": 30,
        "ratio": 0.2
    }
    
    响应格式:
    {
        "status": "success",
        "summary": "生成的摘要文本",
        "method_used": "bart",
        "processing_time": 1.8,
        "quality_metrics": {
            "recall": 0.75,
            "precision": 0.80,
            "f1_score": 0.77
        }
    }
    """
    try:
        # 检查模型是否初始化
        if not summary_model:
            raise HTTPException(status_code=503, detail="摘要生成服务暂时不可用")
        
        # 获取请求参数
        text = request.get('text', '')
        method = request.get('method', 'auto')
        max_length = request.get('max_length', 150)
        min_length = request.get('min_length', 30)
        ratio = request.get('ratio', 0.2)
        
        if not text:
            raise HTTPException(status_code=400, detail="文本内容不能为空")
        
        # 尝试从缓存获取结果
        cache_key = f"api_summary_{hash(text)}_{method}_{max_length}_{min_length}_{ratio}"
        if api_cache:
            cached_result = api_cache.get_cache(cache_key)
            if cached_result is not None:
                logger.info("从API缓存获取摘要生成结果")
                return cached_result
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 根据方法生成摘要
        if method == "bart":
            summary = summary_model.generate_bart_summary(text, max_length, min_length)
        elif method == "textrank":
            summary = summary_model.generate_textrank_summary(text, ratio)
        elif method == "auto":
            summary = summary_model.select_best_summary(text, max_length, min_length)
        else:
            raise HTTPException(status_code=400, detail="不支持的摘要方法")
        
        # 计算处理时间
        processing_time = time.time() - start_time
        
        # 评估摘要质量
        quality_metrics = summary_model.evaluate_summary_quality(text, summary)
        
        # 构建响应
        response = {
            "status": "success",
            "summary": summary,
            "method_used": method,
            "processing_time": round(processing_time, 2),
            "quality_metrics": quality_metrics
        }
        
        # 缓存结果
        if api_cache:
            api_cache.set_cache(cache_key, response, ttl=1800)  # 缓存30分钟
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"摘要生成API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch")
@performance_monitor
@memory_monitor
def batch_generate_summaries(request: Dict[str, Any]):
    """
    批量生成摘要
    
    请求格式:
    {
        "texts": ["文本1", "文本2", "文本3"],
        "method": "bart|textrank|auto",
        "max_length": 150,
        "min_length": 30
    }
    
    响应格式:
    {
        "status": "success",
        "results": [
            {
                "original_text": "文本1",
                "summary": "摘要1",
                "method_used": "bart",
                "processing_time": 0.5
            }
        ]
    }
    """
    try:
        # 检查模型是否初始化
        if not summary_model:
            raise HTTPException(status_code=503, detail="摘要生成服务暂时不可用")
        
        # 获取请求参数
        texts = request.get('texts', [])
        method = request.get('method', 'auto')
        max_length = request.get('max_length', 150)
        min_length = request.get('min_length', 30)
        
        if not texts or not isinstance(texts, list):
            raise HTTPException(status_code=400, detail="文本列表不能为空")
        
        # 尝试从缓存获取结果
        cache_key = f"api_batch_summary_{hash(str(texts))}_{method}_{max_length}_{min_length}"
        if api_cache:
            cached_result = api_cache.get_cache(cache_key)
            if cached_result is not None:
                logger.info("从API缓存获取批量摘要生成结果")
                return cached_result
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 批量生成摘要
        results = summary_model.batch_generate_summaries(texts, method, max_length, min_length)
        
        # 计算总处理时间
        processing_time = time.time() - start_time
        
        # 构建响应
        response = {
            "status": "success",
            "results": results,
            "total_processing_time": round(processing_time, 2),
            "method_used": method
        }
        
        # 缓存结果
        if api_cache:
            api_cache.set_cache(cache_key, response, ttl=1800)  # 缓存30分钟
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量摘要生成API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/keywords")
def generate_keywords(request: Dict[str, Any]):
    """
    生成关键词摘要
    
    请求格式:
    {
        "text": "需要提取关键词的文本",
        "num_keywords": 5
    }
    
    响应格式:
    {
        "status": "success",
        "keywords": ["关键词1", "关键词2"],
        "summary": "关键词1 | 关键词2",
        "keyword_count": 2
    }
    """
    try:
        # 获取请求参数
        text = request.get('text', '')
        num_keywords = request.get('num_keywords', 5)
        
        if not text:
            raise HTTPException(status_code=400, detail="文本内容不能为空")
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 生成关键词摘要
        result = summary_model.generate_keyword_summary(text, num_keywords)
        
        # 计算处理时间
        processing_time = time.time() - start_time
        
        # 构建响应
        response = {
            "status": "success",
            "keywords": result.get("keywords", []),
            "summary": result.get("summary", ""),
            "keyword_count": result.get("keyword_count", 0),
            "processing_time": round(processing_time, 2)
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"关键词摘要API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/multilevel")
def generate_multilevel_summary(request: Dict[str, Any]):
    """
    生成多级摘要
    
    请求格式:
    {
        "text": "需要生成多级摘要的文本",
        "levels": 3
    }
    
    响应格式:
    {
        "status": "success",
        "summaries": [
            {
                "level": 1,
                "summary": "一级摘要",
                "length": 100,
                "method": "BART"
            }
        ]
    }
    """
    try:
        # 获取请求参数
        text = request.get('text', '')
        levels = request.get('levels', 3)
        
        if not text:
            raise HTTPException(status_code=400, detail="文本内容不能为空")
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 生成多级摘要
        summaries = summary_model.generate_multilevel_summary(text, levels)
        
        # 计算处理时间
        processing_time = time.time() - start_time
        
        # 构建响应
        response = {
            "status": "success",
            "summaries": summaries,
            "total_levels": len(summaries),
            "processing_time": round(processing_time, 2)
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"多级摘要API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/complexity")
def analyze_text_complexity(request: Dict[str, Any]):
    """
    分析文本复杂度
    
    请求格式:
    {
        "text": "需要分析的文本"
    }
    
    响应格式:
    {
        "status": "success",
        "complexity_metrics": {
            "sentence_count": 10,
            "word_count": 200,
            "avg_sentence_length": 20.0,
            "unique_words": 150,
            "lexical_diversity": 0.75,
            "text_length": 1000
        }
    }
    """
    try:
        # 获取请求参数
        text = request.get('text', '')
        
        if not text:
            raise HTTPException(status_code=400, detail="文本内容不能为空")
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 分析文本复杂度
        complexity_metrics = summary_model.analyze_text_complexity(text)
        
        # 计算处理时间
        processing_time = time.time() - start_time
        
        # 构建响应
        response = {
            "status": "success",
            "complexity_metrics": complexity_metrics,
            "processing_time": round(processing_time, 2)
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文本复杂度分析API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/context")
def generate_summary_with_context(request: Dict[str, Any]):
    """
    带上下文的摘要生成
    
    请求格式:
    {
        "text": "需要生成摘要的文本",
        "context": "上下文信息",
        "max_length": 150,
        "min_length": 30
    }
    
    响应格式:
    {
        "status": "success",
        "summary": "生成的摘要文本",
        "method_used": "bart",
        "processing_time": 1.2
    }
    """
    try:
        # 获取请求参数
        text = request.get('text', '')
        context = request.get('context', '')
        max_length = request.get('max_length', 150)
        min_length = request.get('min_length', 30)
        
        if not text:
            raise HTTPException(status_code=400, detail="文本内容不能为空")
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 生成带上下文的摘要
        summary = summary_model.generate_summary_with_context(text, context, max_length, min_length)
        
        # 计算处理时间
        processing_time = time.time() - start_time
        
        # 构建响应
        response = {
            "status": "success",
            "summary": summary,
            "method_used": "bart_with_context",
            "processing_time": round(processing_time, 2)
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"带上下文摘要API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/info")
def get_summary_info():
    """
    获取摘要模型信息
    
    响应格式:
    {
        "status": "success",
        "model_info": {
            "name": "BART + TextRank",
            "version": "1.0.0",
            "description": "基于BART和TextRank的摘要模型",
            "supported_methods": ["bart", "textrank", "auto"],
            "max_text_length": 1024
        }
    }
    """
    try:
        # 构建响应
        response = {
            "status": "success",
            "model_info": {
                "name": "BART + TextRank",
                "version": "1.0.0",
                "description": "基于BART和TextRank的摘要模型",
                "supported_methods": ["bart", "textrank", "auto"],
                "max_text_length": 1024,
                "min_text_length": 10
            }
        }
        
        return response
        
    except Exception as e:
        logger.error(f"获取摘要模型信息API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 导出 APIRouter 供主应用使用
__all__ = ["router"]