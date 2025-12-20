import re
import nltk
import string
from typing import List, Dict, Any, Optional
import logging
from bs4 import BeautifulSoup

# 下载必要的NLTK数据
try:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')
except:
    pass

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextUtils:
    """文本处理工具类"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        清洗文本
        
        Args:
            text: 原始文本
            
        Returns:
            清洗后的文本
        """
        if not text or not isinstance(text, str):
            return ""
        
        try:
            # 转换为小写
            text = text.lower()
            
            # 移除HTML标签
            text = BeautifulSoup(text, "html.parser").get_text()
            
            # 移除URL
            text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
            
            # 移除特殊字符和标点
            text = re.sub(r'[%s]' % re.escape(string.punctuation), ' ', text)
            
            # 移除数字
            text = re.sub(r'\d+', '', text)
            
            # 移除多余空白
            text = re.sub(r'\s+', ' ', text).strip()
            
            logger.info(f"文本清洗完成，处理前长度: {len(text)}")
            return text
            
        except Exception as e:
            logger.error(f"文本清洗失败: {e}")
            return text
    
    @staticmethod
    def tokenize_text(text: str, language: str = "english") -> List[str]:
        """
        文本分词
        
        Args:
            text: 文本内容
            language: 语言类型
            
        Returns:
            分词结果列表
        """
        if not text or not isinstance(text, str):
            return []
        
        try:
            # 使用nltk进行分词
            tokens = nltk.word_tokenize(text, language=language)
            
            logger.info(f"文本分词完成，分词数: {len(tokens)}")
            return tokens
            
        except Exception as e:
            logger.error(f"文本分词失败: {e}")
            return []
    
    @staticmethod
    def remove_stopwords(tokens: List[str], language: str = "english") -> List[str]:
        """
        移除停用词
        
        Args:
            tokens: 分词结果列表
            language: 语言类型
            
        Returns:
            移除停用词后的分词列表
        """
        if not tokens or not isinstance(tokens, list):
            return []
        
        try:
            # 获取停用词列表
            stopwords = set(nltk.corpus.stopwords.words(language))
            
            # 移除停用词
            filtered_tokens = [token for token in tokens if token not in stopwords]
            
            logger.info(f"移除停用词完成，剩余词数: {len(filtered_tokens)}")
            return filtered_tokens
            
        except Exception as e:
            logger.error(f"移除停用词失败: {e}")
            return tokens
    
    @staticmethod
    def lemmatize_tokens(tokens: List[str], language: str = "english") -> List[str]:
        """
        词形还原
        
        Args:
            tokens: 分词结果列表
            language: 语言类型
            
        Returns:
            词形还原后的分词列表
        """
        if not tokens or not isinstance(tokens, list):
            return []
        
        try:
            # 获取词形还原器
            if language == "english":
                lemmatizer = nltk.WordNetLemmatizer()
            else:
                # 简化的中文词形还原（实际应用中需要更复杂的处理）
                lemmatizer = lambda x: x  # 中文暂不处理
            
            # 词形还原
            lemmatized_tokens = [lemmatizer.lemmatize(token) for token in tokens]
            
            logger.info(f"词形还原完成，词数: {len(lemmatized_tokens)}")
            return lemmatized_tokens
            
        except Exception as e:
            logger.error(f"词形还原失败: {e}")
            return tokens
    
    @staticmethod
    def extract_keywords(text: str, num_keywords: int = 10, language: str = "english") -> List[str]:
        """
        提取关键词
        
        Args:
            text: 文本内容
            num_keywords: 关键词数量
            language: 语言类型
            
        Returns:
            关键词列表
        """
        if not text or not isinstance(text, str):
            return []
        
        try:
            # 清洗文本
            cleaned_text = TextUtils.clean_text(text)
            
            # 分词
            tokens = TextUtils.tokenize_text(cleaned_text, language)
            
            # 移除停用词
            filtered_tokens = TextUtils.remove_stopwords(tokens, language)
            
            # 词形还原
            lemmatized_tokens = TextUtils.lemmatize_tokens(filtered_tokens, language)
            
            # 计算词频
            from collections import Counter
            word_freq = Counter(lemmatized_tokens)
            
            # 获取前N个关键词
            keywords = [word for word, freq in word_freq.most_common(num_keywords)]
            
            logger.info(f"提取关键词完成，关键词数: {len(keywords)}")
            return keywords
            
        except Exception as e:
            logger.error(f"提取关键词失败: {e}")
            return []
    
    @staticmethod
    def extract_ngrams(text: str, n: int = 2, num_ngrams: int = 10) -> List[str]:
        """
        提取N-grams
        
        Args:
            text: 文本内容
            n: N-grams大小
            num_ngrams: 提取数量
            
        Returns:
            N-grams列表
        """
        if not text or not isinstance(text, str):
            return []
        
        try:
            # 清洗文本
            cleaned_text = TextUtils.clean_text(text)
            
            # 分词
            tokens = TextUtils.tokenize_text(cleaned_text)
            
            # 移除停用词
            filtered_tokens = TextUtils.remove_stopwords(tokens)
            
            # 生成N-grams
            from nltk.util import ngrams
            ngram_list = list(ngrams(filtered_tokens, n))
            
            # 转换为字符串
            ngrams_str = [' '.join(gram) for gram in ngram_list]
            
            # 计算频率
            from collections import Counter
            ngram_freq = Counter(ngrams_str)
            
            # 获取前N个N-grams
            top_ngrams = [ngram for ngram, freq in ngram_freq.most_common(num_ngrams)]
            
            logger.info(f"提取{n}-grams完成，数量: {len(top_ngrams)}")
            return top_ngrams
            
        except Exception as e:
            logger.error(f"提取{n}-grams失败: {e}")
            return []
    
    @staticmethod
    def calculate_text_stats(text: str) -> Dict[str, Any]:
        """
        计算文本统计信息
        
        Args:
            text: 文本内容
            
        Returns:
            文本统计信息字典
        """
        if not text or not isinstance(text, str):
            return {}
        
        try:
            # 清洗文本
            cleaned_text = TextUtils.clean_text(text)
            
            # 分词
            tokens = TextUtils.tokenize_text(cleaned_text)
            
            # 移除停用词
            filtered_tokens = TextUtils.remove_stopwords(tokens)
            
            # 词形还原
            lemmatized_tokens = TextUtils.lemmatize_tokens(filtered_tokens)
            
            # 计算统计信息
            stats = {
                "original_length": len(text),
                "cleaned_length": len(cleaned_text),
                "token_count": len(tokens),
                "filtered_token_count": len(filtered_tokens),
                "lemmatized_token_count": len(lemmatized_tokens),
                "unique_tokens": len(set(tokens)),
                "unique_filtered_tokens": len(set(filtered_tokens)),
                "unique_lemmatized_tokens": len(set(lemmatized_tokens)),
                "avg_token_length": sum(len(token) for token in tokens) / len(tokens) if tokens else 0,
                "lexical_diversity": len(set(tokens)) / len(tokens) if tokens else 0
            }
            
            logger.info(f"计算文本统计完成: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"计算文本统计失败: {e}")
            return {}
    
    @staticmethod
    def detect_language(text: str) -> str:
        """
        检测文本语言
        
        Args:
            text: 文本内容
            
        Returns:
            检测到的语言
        """
        if not text or not isinstance(text, str):
            return "unknown"
        
        try:
            # 简单的语言检测（实际应用中可以使用更复杂的库如langdetect）
            # 这里使用基于字符的简单检测
            chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', text))
            english_chars = len(re.findall(r'[a-zA-Z]', text))
            
            if chinese_chars > english_chars * 2:
                return "chinese"
            elif english_chars > chinese_chars * 2:
                return "english"
            else:
                return "mixed"
                
        except Exception as e:
            logger.error(f"语言检测失败: {e}")
            return "unknown"
    
    @staticmethod
    def extract_sentences(text: str, language: str = "english") -> List[str]:
        """
        提取句子
        
        Args:
            text: 文本内容
            language: 语言类型
            
        Returns:
            句子列表
        """
        if not text or not isinstance(text, str):
            return []
        
        try:
            # 使用nltk进行句子分割
            sentences = nltk.sent_tokenize(text, language=language)
            
            logger.info(f"提取句子完成，句子数: {len(sentences)}")
            return sentences
            
        except Exception as e:
            logger.error(f"提取句子失败: {e}")
            return []
    
    @staticmethod
    def summarize_text(text: str, ratio: float = 0.2) -> str:
        """
        文本摘要（简化版）
        
        Args:
            text: 文本内容
            ratio: 摘要比例
            
        Returns:
            摘要文本
        """
        if not text or not isinstance(text, str):
            return ""
        
        try:
            # 提取句子
            sentences = TextUtils.extract_sentences(text)
            
            # 计算句子重要性（简化版：按位置和长度）
            sentence_scores = []
            for i, sentence in enumerate(sentences):
                score = len(sentence) * (1 - i / len(sentences))
                sentence_scores.append((score, i, sentence))
            
            # 按分数排序
            sentence_scores.sort(reverse=True)
            
            # 选择前ratio比例的句子
            num_sentences = max(1, int(len(sentences) * ratio))
            selected_sentences = [sentence_scores[i][2] for i in range(num_sentences)]
            
            # 按原始顺序排序
            selected_sentences.sort(key=lambda x: sentences.index(x))
            
            # 合并句子
            summary = " ".join(selected_sentences)
            
            logger.info(f"生成文本摘要完成，长度: {len(summary)}")
            return summary
            
        except Exception as e:
            logger.error(f"生成文本摘要失败: {e}")
            return text[:100]  # 返回前100个字符作为简化摘要
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """
        文本规范化
        
        Args:
            text: 原始文本
            
        Returns:
            规范化后的文本
        """
        if not text or not isinstance(text, str):
            return ""
        
        try:
            # 转换为小写
            text = text.lower()
            
            # 移除标点（保留基本标点）
            text = re.sub(r'[^\w\s.,!?;:\'"()\[\]{}-]', '', text)
            
            # 标准化空白
            text = re.sub(r'\s+', ' ', text).strip()
            
            logger.info(f"文本规范化完成，处理前长度: {len(text)}")
            return text
            
        except Exception as e:
            logger.error(f"文本规范化失败: {e}")
            return text
    
    @staticmethod
    def extract_entities_from_text(text: str) -> Dict[str, List[str]]:
        """
        从文本中提取实体（简化版）
        
        Args:
            text: 文本内容
            
        Returns:
            实体字典
        """
        if not text or not isinstance(text, str):
            return {}
        
        try:
            # 简化的实体提取（实际应用中应使用专门的NER模型）
            entities = {
                "persons": re.findall(r'([A-Z][a-z]+(?: [A-Z][a-z]+)*)', text),
                "organizations": re.findall(r'([A-Z][a-z]+(?: [A-Z][a-z]+)*(?: Inc\.| Ltd\.| Corp\.| LLC)?)', text),
                "locations": re.findall(r'([A-Z][a-z]+(?: [A-Z][a-z]+)*(?: Street| Avenue| Road| City| State| Country))', text),
                "dates": re.findall(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', text)
            }
            
            # 去重
            for key in entities:
                entities[key] = list(set(entities[key]))
            
            logger.info(f"提取实体完成: {entities}")
            return entities
            
        except Exception as e:
            logger.error(f"提取实体失败: {e}")
            return {}



