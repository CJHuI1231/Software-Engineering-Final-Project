import logging
import re
from typing import List, Dict, Any

# 尝试导入可选依赖
try:
    import nltk
    HAS_NLTK = True
except ImportError:
    HAS_NLTK = False

try:
    import spacy
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False

try:
    from transformers import pipeline
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

try:
    from summa import summarizer
    HAS_SUMMA = True
except ImportError:
    HAS_SUMMA = False

try:
    from summa import keywords
    HAS_KEYWORDS = True
except ImportError:
    HAS_KEYWORDS = False

# 导入工具类
try:
    from ..utils.cache_manager import (
        CacheManager, 
        ModelCacheManager, 
        BatchProcessingManager,
        performance_monitor,
        memory_monitor,
        async_processing
    )
    from ..utils.config_manager import ConfigManager
    HAS_UTILS = True
except ImportError:
    HAS_UTILS = False
from ..utils.config_manager import ConfigManager

# 下载必要的NLTK数据
try:
    nltk.download('punkt')
    nltk.download('stopwords')
except:
    pass

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SummaryModel:
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化摘要模型
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.nlp = None
        self.transformer_pipeline = None
        self.cache_manager = None
        self.model_cache = None
        self.batch_processor = None
        
        # 初始化缓存管理器
        if HAS_UTILS:
            cache_config = self.config.get('cache', {
                'type': 'memory',
                'ttl': 3600
            })
            self.cache_manager = CacheManager(cache_config)
            self.model_cache = ModelCacheManager(cache_config)
            
            # 初始化批量处理管理器
            self.batch_processor = BatchProcessingManager(
                max_workers=self.config.get('max_workers', 4),
                timeout=self.config.get('timeout', 30)
            )
        else:
            logger.warning("工具类未安装，跳过性能优化初始化")
        
        # 尝试加载spaCy模型
        if HAS_SPACY:
            try:
                nlp_key = "zh_core_web_sm"
                if self.model_cache:
                    self.nlp = self.model_cache.get_model(nlp_key)
                if not self.nlp:
                    self.nlp = spacy.load(nlp_key)
                    if self.model_cache:
                        self.model_cache.cache_model(nlp_key, self.nlp)
                    logger.info("成功加载spaCy中文模型")
                else:
                    logger.info("从缓存加载spaCy中文模型")
            except Exception as e:
                logger.error(f"spaCy模型加载失败: {e}")
                raise RuntimeError(f"无法加载spaCy模型: {e}")
        else:
            logger.warning("spaCy未安装，spaCy相关功能将不可用")
        
        # 尝试加载transformers模型
        if HAS_TRANSFORMERS:
            try:
                transformer_key = "bart-large-cnn"
                if self.model_cache:
                    self.transformer_pipeline = self.model_cache.get_model(transformer_key)
                if not self.transformer_pipeline:
                    self.transformer_pipeline = pipeline(
                        "summarization",
                        model="facebook/bart-large-cnn",
                        tokenizer="facebook/bart-large-cnn"
                    )
                    if self.model_cache:
                        self.model_cache.cache_model(transformer_key, self.transformer_pipeline)
                    logger.info("成功加载transformers摘要模型")
                else:
                    logger.info("从缓存加载transformers摘要模型")
            except Exception as e:
                logger.error(f"transformers模型加载失败: {e}")
                raise RuntimeError(f"无法加载transformers模型: {e}")
        else:
            logger.warning("transformers未安装，transformers相关功能将不可用")
        
        # 检查是否至少有一个摘要方法可用
        if not self.nlp and not self.transformer_pipeline:
            raise RuntimeError("无法加载任何摘要模型，请确保spaCy或transformers已安装")
    
    @performance_monitor
    @memory_monitor
    def generate_bart_summary(self, text: str, max_length: int = 150, min_length: int = 30) -> str:
        """
        使用BART模型生成摘要
        
        Args:
            text: 需要生成摘要的文本
            max_length: 摘要最大长度
            min_length: 摘要最小长度
            
        Returns:
            生成的摘要
        """
        if not text or not isinstance(text, str):
            return ""
        
        try:
            # 检查transformers是否可用
            if not self.transformer_pipeline:
                logger.warning("transformers未安装，无法使用BART摘要")
                # 提供简化的回退方法
                return self._generate_simple_summary(text, max_length, min_length)
            
            # 生成缓存键
            if self.cache_manager:
                cache_key = f"bart_summary_{hash(text)}_{max_length}_{min_length}"
                cached_result = self.cache_manager.get_cache(cache_key)
                if cached_result is not None:
                    logger.info("从缓存获取BART摘要结果")
                    return cached_result
            
            # 确保文本长度适合模型
            if len(text) > 1024:  # BART模型的限制
                text = text[:1024]
            
            # 使用transformers管道生成摘要
            summary = self.transformer_pipeline(
                text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False
            )
            
            # 提取摘要文本
            summary_text = summary[0]['summary_text']
            
            # 缓存结果
            self.cache_manager.set_cache(cache_key, summary_text)
            
            logger.info(f"使用BART生成摘要，长度: {len(summary_text)}")
            return summary_text
            
        except Exception as e:
            logger.error(f"BART摘要生成失败: {e}")
            return ""
    
    @performance_monitor
    @memory_monitor
    def generate_textrank_summary(self, text: str, ratio: float = 0.2, words: int = None) -> str:
        """
        使用TextRank算法生成摘要
        
        Args:
            text: 需要生成摘要的文本
            ratio: 摘要比例（0-1）
            words: 摘要字数（优先于ratio）
            
        Returns:
            生成的摘要
        """
        if not text or not isinstance(text, str):
            return ""
        
        try:
            # 检查summa是否可用
            if not HAS_SUMMA:
                logger.warning("summa未安装，无法使用TextRank摘要")
                return self._generate_simple_summary(text)
            
            # 生成缓存键
            if self.cache_manager:
                cache_key = f"textrank_summary_{hash(text)}_{ratio}_{words}"
                cached_result = self.cache_manager.get_cache(cache_key)
                if cached_result is not None:
                    logger.info("从缓存获取TextRank摘要结果")
                    return cached_result
            
            # 使用summa库的TextRank实现
            if words:
                summary = summarizer.summarize(text, words=words)
            else:
                summary = summarizer.summarize(text, ratio=ratio)
            
            # 缓存结果
            self.cache_manager.set_cache(cache_key, summary)
            
            logger.info(f"使用TextRank生成摘要，长度: {len(summary)}")
            return summary
            
        except Exception as e:
            logger.error(f"TextRank摘要生成失败: {e}")
            return ""
    
    def select_best_summary(self, text: str, max_length: int = 150, min_length: int = 30) -> str:
        """
        根据文本特性选择最佳摘要方法
        
        Args:
            text: 需要生成摘要的文本
            max_length: 摘要最大长度
            min_length: 摘要最小长度
            
        Returns:
            最佳摘要
        """
        if not text or not isinstance(text, str):
            return ""
        
        try:
            # 分析文本特性
            text_length = len(text)
            word_count = len(text.split())
            
            # 根据文本长度选择方法
            if text_length > 1000:  # 长文本使用BART
                logger.info("长文本，使用BART模型")
                return self.generate_bart_summary(text, max_length, min_length)
            elif word_count > 500:  # 中等长度文本使用TextRank
                logger.info("中等长度文本，使用TextRank算法")
                return self.generate_textrank_summary(text, ratio=0.2)
            else:  # 短文本直接返回
                logger.info("短文本，直接返回")
                return text[:max_length]
                
        except Exception as e:
            logger.error(f"选择最佳摘要方法失败: {e}")
            return ""
    
    def generate_keyword_summary(self, text: str, num_keywords: int = 5) -> Dict[str, Any]:
        """
        生成关键词摘要
        
        Args:
            text: 需要提取关键词的文本
            num_keywords: 关键词数量
            
        Returns:
            关键词摘要
        """
        if not text or not isinstance(text, str):
            return {"keywords": [], "summary": ""}
        
        try:
            # 提取关键词
            keywords_list = keywords.keywords(text, words=num_keywords).split('\n')
            keywords_list = [kw.strip() for kw in keywords_list if kw.strip()]
            
            # 生成基于关键词的摘要
            if keywords_list:
                keyword_summary = " | ".join(keywords_list)
            else:
                keyword_summary = ""
            
            result = {
                "keywords": keywords_list,
                "summary": keyword_summary,
                "keyword_count": len(keywords_list)
            }
            
            logger.info(f"生成关键词摘要，关键词数量: {len(keywords_list)}")
            return result
            
        except Exception as e:
            logger.error(f"关键词摘要生成失败: {e}")
            return {"keywords": [], "summary": "", "keyword_count": 0}
    
    def generate_multilevel_summary(self, text: str, levels: int = 3) -> List[Dict[str, Any]]:
        """
        生成多级摘要
        
        Args:
            text: 需要生成多级摘要的文本
            levels: 摘要级别数量
            
        Returns:
            多级摘要列表
        """
        if not text or not isinstance(text, str):
            return []
        
        try:
            summaries = []
            
            for i in range(1, levels + 1):
                # 根据级别调整摘要长度
                ratio = 1.0 / (i * 2)  # 每级摘要长度减半
                max_length = max(30, int(150 / i))  # 摘要长度递减
                
                if i == 1:
                    # 第一级使用BART
                    summary = self.generate_bart_summary(text, max_length=max_length)
                else:
                    # 后续级别使用TextRank
                    summary = self.generate_textrank_summary(summary, ratio=ratio)
                
                summaries.append({
                    "level": i,
                    "summary": summary,
                    "length": len(summary),
                    "method": "BART" if i == 1 else "TextRank"
                })
            
            logger.info(f"生成多级摘要，共 {len(summaries)} 级")
            return summaries
            
        except Exception as e:
            logger.error(f"多级摘要生成失败: {e}")
            return []
    
    def analyze_text_complexity(self, text: str) -> Dict[str, Any]:
        """
        分析文本复杂度
        
        Args:
            text: 需要分析的文本
            
        Returns:
            文本复杂度分析结果
        """
        if not text or not isinstance(text, str):
            return {}
        
        try:
            # 使用spaCy分析文本
            doc = self.nlp(text)
            
            # 计算各种复杂度指标
            sentence_count = len(list(doc.sents))
            word_count = len([token for token in doc if not token.is_punct])
            avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
            unique_words = len(set([token.text.lower() for token in doc if not token.is_punct]))
            lexical_diversity = unique_words / word_count if word_count > 0 else 0
            
            result = {
                "sentence_count": sentence_count,
                "word_count": word_count,
                "avg_sentence_length": avg_sentence_length,
                "unique_words": unique_words,
                "lexical_diversity": lexical_diversity,
                "text_length": len(text)
            }
            
            logger.info(f"文本复杂度分析完成，句子数: {sentence_count}, 词数: {word_count}")
            return result
            
        except Exception as e:
            logger.error(f"文本复杂度分析失败: {e}")
            return {}
    
    def generate_summary_with_context(self, text: str, context: str = "", 
                                 max_length: int = 150, min_length: int = 30) -> str:
        """
        带上下文的摘要生成
        
        Args:
            text: 需要生成摘要的文本
            context: 上下文信息
            max_length: 摘要最大长度
            min_length: 摘要最小长度
            
        Returns:
            带上下文的摘要
        """
        if not text or not isinstance(text, str):
            return ""
        
        try:
            # 组合文本和上下文
            combined_text = f"{context}\n\n{text}" if context else text
            
            # 生成摘要
            summary = self.generate_bart_summary(combined_text, max_length, min_length)
            
            logger.info(f"带上下文摘要生成完成，长度: {len(summary)}")
            return summary
            
        except Exception as e:
            logger.error(f"带上下文摘要生成失败: {e}")
            return ""
    
    @performance_monitor
    def batch_generate_summaries(self, texts: List[str], method: str = "auto", 
                             max_length: int = 150, min_length: int = 30) -> List[Dict[str, Any]]:
        """
        批量生成摘要
        
        Args:
            texts: 文本列表
            method: 摘要方法
            max_length: 摘要最大长度
            min_length: 摘要最小长度
            
        Returns:
            摘要结果列表
        """
        if not texts or not isinstance(texts, list):
            return []
        
        try:
            # 根据方法选择处理函数
            if method == "bart":
                process_func = lambda text: self.generate_bart_summary(text, max_length, min_length)
            elif method == "textrank":
                process_func = lambda text: self.generate_textrank_summary(text, ratio=0.2)
            elif method == "auto":
                process_func = lambda text: self.select_best_summary(text, max_length, min_length)
            else:
                process_func = lambda text: ""
            
            # 并行处理文本
            if self.batch_processor:
                summaries = self.batch_processor.process_batch(texts, process_func)
            else:
                # 回退到顺序处理
                logger.warning("批量处理管理器不可用，使用顺序处理")
                summaries = []
                for text in texts:
                    if method == "bart":
                        summary = self.generate_bart_summary(text, max_length, min_length)
                    elif method == "textrank":
                        summary = self.generate_textrank_summary(text, ratio=0.2)
                    elif method == "auto":
                        summary = self.select_best_summary(text, max_length, min_length)
                    else:
                        summary = ""
                    
                    summaries.append(summary)
            
            # 构建结果
            results = []
            for i, text in enumerate(texts):
                # 初始化summaries列表为空
                if 'summaries' not in locals():
                    summaries = []
                summary = summaries[i] if i < len(summaries) else ""
                results.append({
                    "original_text": text,
                    "summary": summary,
                    "method_used": method,
                    "summary_length": len(summary)
                })
            
            logger.info(f"批量摘要生成完成，共处理 {len(texts)} 个文本")
            return results
            
        except Exception as e:
            logger.error(f"批量摘要生成失败: {e}")
            # 回退到顺序处理
            results = []
            for text in texts:
                try:
                    if method == "bart":
                        summary = self.generate_bart_summary(text, max_length, min_length)
                    elif method == "textrank":
                        summary = self.generate_textrank_summary(text, ratio=0.2)
                    elif method == "auto":
                        summary = self.select_best_summary(text, max_length, min_length)
                    else:
                        summary = ""
                    
                    results.append({
                        "original_text": text,
                        "summary": summary,
                        "method_used": method,
                        "summary_length": len(summary)
                    })
                except Exception as inner_e:
                    logger.error(f"单个摘要生成失败: {inner_e}")
                    results.append({
                        "original_text": text,
                        "summary": "",
                        "method_used": method,
                        "error": str(inner_e)
                    })
            return results
    
    def evaluate_summary_quality(self, original_text: str, summary: str) -> Dict[str, float]:
        """
        评估摘要质量
        
        Args:
            original_text: 原始文本
            summary: 摘要文本
            
        Returns:
            摘要质量评分
        """
        if not original_text or not summary or not isinstance(original_text, str) or not isinstance(summary, str):
            return {}
        
        try:
            # 计算各种质量指标
            original_words = set(original_text.lower().split())
            summary_words = set(summary.lower().split())
            
            # 计算ROUGE-like指标（简化版）
            recall = len(original_words.intersection(summary_words)) / len(original_words) if original_words else 0
            precision = len(original_words.intersection(summary_words)) / len(summary_words) if summary_words else 0
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            # 计算覆盖率
            coverage = len(summary) / len(original_text) if len(original_text) > 0 else 0
            
            result = {
                "recall": recall,
                "precision": precision,
                "f1_score": f1_score,
                "coverage": coverage,
                "summary_length": len(summary),
                "original_length": len(original_text)
            }
            
            logger.info(f"摘要质量评估完成，F1分数: {f1_score:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"摘要质量评估失败: {e}")
            return {}
