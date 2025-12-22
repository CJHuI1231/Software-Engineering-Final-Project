import pytest
import sys
import os
import tempfile
import shutil

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nlp.utils.file_utils import FileUtils
from nlp.utils.text_utils import TextUtils
from nlp.utils.error_handler import ErrorHandler
from nlp.utils.config_manager import ConfigManager

class TestUtils:
    """工具函数测试类"""
    
    def test_file_utils(self):
        """测试文件工具功能"""
        file_utils = FileUtils()
        
        # 测试文件信息获取
        test_file = __file__  # 使用当前测试文件作为测试文件
        file_info = file_utils.get_file_info(test_file)
        
        # 验证结果
        assert isinstance(file_info, dict)
        assert "path" in file_info
        assert "size" in file_info
        assert "modified_time" in file_info
        assert "is_readable" in file_info
        assert "is_writable" in file_info
        assert "extension" in file_info
        assert "mime_type" in file_info
        
        # 验证文件信息值
        assert file_info["path"] == test_file
        assert file_info["size"] > 0
        assert file_info["is_readable"] is True
        assert file_info["is_writable"] is True
        assert file_info["extension"] == ".py"
    
    def test_text_utils(self):
        """测试文本工具功能"""
        text_utils = TextUtils()
        
        # 测试文本清洗
        test_text = "  这是一个测试文本，包含  多余的  空格和标点！  "
        cleaned_text = text_utils.clean_text(test_text)
        
        # 验证结果
        assert isinstance(cleaned_text, str)
        assert cleaned_text == "这是一个测试文本包含多余的空格和标点"
        
        # 测试文本分词
        tokens = text_utils.tokenize_text(cleaned_text)
        
        # 验证结果
        assert isinstance(tokens, list)
        assert len(tokens) > 0
        
        # 测试停用词移除
        filtered_tokens = text_utils.remove_stopwords(tokens)
        
        # 验证结果
        assert isinstance(filtered_tokens, list)
        assert len(filtered_tokens) <= len(tokens)
        
        # 测试关键词提取
        keywords = text_utils.extract_keywords(cleaned_text, num_keywords=3)
        
        # 验证结果
        assert isinstance(keywords, list)
        assert len(keywords) == 3
        
        # 测试N-grams提取
        ngrams = text_utils.extract_ngrams(cleaned_text, n=2, num_ngrams=2)
        
        # 验证结果
        assert isinstance(ngrams, list)
        assert len(ngrams) == 2
    
    def test_error_handler(self):
        """测试错误处理功能"""
        error_handler = ErrorHandler()
        
        # 测试错误处理
        try:
            raise ValueError("测试错误")
        except Exception as e:
            error_response = error_handler.handle_api_error(e)
            
            # 验证结果
            assert isinstance(error_response, dict)
            assert "status" in error_response
            assert "message" in error_response
            assert error_response["status"] == "error"
            assert "测试错误" in error_response["message"]
    
    def test_config_manager(self):
        """测试配置管理功能"""
        config_manager = ConfigManager()
        
        # 测试默认配置创建
        default_config = config_manager.create_default_config()
        
        # 验证结果
        assert isinstance(default_config, dict)
        assert "api" in default_config
        assert "logging" in default_config
        assert "entity_recognition" in default_config
        assert "summary" in default_config
        
        # 测试配置合并
        config1 = {"key1": "value1"}
        config2 = {"key2": "value2", "key1": "value1_updated"}
        merged_config = config_manager.merge_configs(config1, config2)
        
        # 验证结果
        assert isinstance(merged_config, dict)
        assert "key1" in merged_config
        assert "key2" in merged_config
        assert merged_config["key1"] == "value1_updated"  # 后面的配置应该覆盖前面的
        assert merged_config["key2"] == "value2"
    
    def test_temp_file_creation(self):
        """测试临时文件创建功能"""
        file_utils = FileUtils()
        
        # 创建临时文件
        temp_file_path = file_utils.create_temp_file("测试内容", suffix=".txt")
        
        # 验证结果
        assert os.path.exists(temp_file_path)
        assert os.path.isfile(temp_file_path)
        
        # 验证文件内容
        with open(temp_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            assert content == "测试内容"
        
        # 清理临时文件
        os.remove(temp_file_path)
        assert not os.path.exists(temp_file_path)
    
    def test_file_validation(self):
        """测试文件验证功能"""
        file_utils = FileUtils()
        
        # 测试有效文件
        test_file = __file__
        is_valid = file_utils.validate_file_path(test_file)
        
        # 验证结果
        assert is_valid is True
        
        # 测试无效文件
        invalid_file = "不存在的文件路径"
        is_valid = file_utils.validate_file_path(invalid_file)
        
        # 验证结果
        assert is_valid is False
    
    def test_text_processing_pipeline(self):
        """测试文本处理管道"""
        text_utils = TextUtils()
        
        # 测试文本
        test_text = "  这是一个测试文本，包含  多余的  空格、标点和特殊字符！@#$%^&*()  "
        
        # 执行完整处理管道
        cleaned_text = text_utils.clean_text(test_text)
        tokens = text_utils.tokenize_text(cleaned_text)
        filtered_tokens = text_utils.remove_stopwords(tokens)
        lemmatized_tokens = text_utils.lemmatize_tokens(filtered_tokens)
        keywords = text_utils.extract_keywords(cleaned_text, num_keywords=3)
        
        # 验证结果
        assert isinstance(cleaned_text, str)
        assert isinstance(tokens, list)
        assert isinstance(filtered_tokens, list)
        assert isinstance(lemmatized_tokens, list)
        assert isinstance(keywords, list)
        
        # 验证处理结果
        assert len(filtered_tokens) <= len(tokens)
        assert len(lemmatized_tokens) == len(filtered_tokens)
        assert len(keywords) == 3
    
    def test_text_complexity_analysis(self):
        """测试文本复杂度分析"""
        text_utils = TextUtils()
        
        # 测试文本
        test_text = "这是一个测试文本。它包含多个句子，每个句子都有不同的长度和结构。我们需要分析文本的复杂度指标。"
        
        # 分析文本复杂度
        complexity_metrics = text_utils.calculate_text_stats(test_text)
        
        # 验证结果
        assert isinstance(complexity_metrics, dict)
        assert "original_length" in complexity_metrics
        assert "cleaned_length" in complexity_metrics
        assert "token_count" in complexity_metrics
        assert "filtered_token_count" in complexity_metrics
        assert "lemmatized_token_count" in complexity_metrics
        assert "unique_tokens" in complexity_metrics
        assert "unique_filtered_tokens" in complexity_metrics
        assert "unique_lemmatized_tokens" in complexity_metrics
        assert "avg_token_length" in complexity_metrics
        assert "lexical_diversity" in complexity_metrics
        
        # 验证指标值
        assert complexity_metrics["original_length"] > 0
        assert complexity_metrics["cleaned_length"] > 0
        assert complexity_metrics["token_count"] > 0
        assert complexity_metrics["avg_token_length"] > 0
        assert 0 <= complexity_metrics["lexical_diversity"] <= 1
    
    def test_language_detection(self):
        """测试语言检测功能"""
        text_utils = TextUtils()
        
        # 测试中文文本
        chinese_text = "这是一个中文文本"
        chinese_language = text_utils.detect_language(chinese_text)
        
        # 验证结果
        assert chinese_language == "chinese" or chinese_language == "mixed"
        
        # 测试英文文本
        english_text = "This is an English text"
        english_language = text_utils.detect_language(english_text)
        
        # 验证结果
        assert english_language == "english" or english_language == "mixed"
        
        # 测试混合文本
        mixed_text = "This is a mixed text with 中文"
        mixed_language = text_utils.detect_language(mixed_text)
        
        # 验证结果
        assert mixed_language == "mixed"

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__])




