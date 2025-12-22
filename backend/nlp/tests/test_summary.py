import pytest
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nlp.summary.summary_model import SummaryModel

class TestSummaryModel:
    """摘要模型测试类"""
    
    @pytest.fixture
    def summary_model(self):
        """创建摘要模型实例"""
        return SummaryModel()
    
    def test_generate_bart_summary(self, summary_model):
        """测试BART摘要生成功能"""
        # 测试文本
        test_text = "这是一个测试文本，用于测试BART摘要生成功能。文本包含多个句子，每个句子都有不同的内容和结构。我们需要确保摘要能够准确地提取文本的主要信息。"
        
        # 生成摘要
        summary = summary_model.generate_bart_summary(test_text, max_length=50)
        
        # 验证结果
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert len(summary) <= 50  # 确保长度不超过限制
        
        # 验证摘要内容
        assert "测试" in summary
        assert "文本" in summary
        assert "摘要" in summary
    
    def test_generate_textrank_summary(self, summary_model):
        """测试TextRank摘要生成功能"""
        # 测试文本
        test_text = "这是一个测试文本，用于测试TextRank摘要生成功能。文本包含多个句子，每个句子都有不同的内容和结构。我们需要确保摘要能够准确地提取文本的主要信息。"
        
        # 生成摘要
        summary = summary_model.generate_textrank_summary(test_text, ratio=0.2)
        
        # 验证结果
        assert isinstance(summary, str)
        assert len(summary) > 0
        
        # 验证摘要内容
        assert "测试" in summary
        assert "文本" in summary
        assert "摘要" in summary
    
    def test_select_best_summary(self, summary_model):
        """测试最佳摘要选择功能"""
        # 测试文本
        test_text = "这是一个较长的测试文本，用于测试最佳摘要选择功能。文本包含多个句子，每个句子都有不同的内容和结构。我们需要确保系统能够根据文本特性选择最合适的摘要方法。"
        
        # 选择最佳摘要
        summary = summary_model.select_best_summary(test_text)
        
        # 验证结果
        assert isinstance(summary, str)
        assert len(summary) > 0
        
        # 验证摘要内容
        assert "测试" in summary
        assert "文本" in summary
        assert "摘要" in summary
    
    def test_generate_keyword_summary(self, summary_model):
        """测试关键词摘要生成功能"""
        # 测试文本
        test_text = "张三在阿里巴巴工作，李四在腾讯上班，王五在百度实习。"
        
        # 生成关键词摘要
        result = summary_model.generate_keyword_summary(test_text, num_keywords=3)
        
        # 验证结果
        assert isinstance(result, dict)
        assert "keywords" in result
        assert "summary" in result
        assert "keyword_count" in result
        
        # 验证关键词列表
        keywords = result["keywords"]
        assert isinstance(keywords, list)
        assert len(keywords) == 3  # 确保返回3个关键词
        
        # 验证关键词内容
        assert "张三" in keywords or "李四" in keywords or "王五" in keywords
        assert "阿里巴巴" in keywords or "腾讯" in keywords or "百度" in keywords
    
    def test_generate_multilevel_summary(self, summary_model):
        """测试多级摘要生成功能"""
        # 测试文本
        test_text = "这是一个测试文本，用于测试多级摘要生成功能。文本包含多个句子，每个句子都有不同的内容和结构。我们需要确保系统能够生成不同级别的摘要。"
        
        # 生成多级摘要
        summaries = summary_model.generate_multilevel_summary(test_text, levels=2)
        
        # 验证结果
        assert isinstance(summaries, list)
        assert len(summaries) == 2  # 确保返回2级摘要
        
        # 验证每级摘要
        for summary in summaries:
            assert "level" in summary
            assert "summary" in summary
            assert "length" in summary
            assert "method" in summary
    
    def test_analyze_text_complexity(self, summary_model):
        """测试文本复杂度分析功能"""
        # 测试文本
        test_text = "这是一个测试文本，用于测试文本复杂度分析功能。文本包含多个句子，每个句子都有不同的内容和结构。"
        
        # 分析文本复杂度
        complexity_metrics = summary_model.analyze_text_complexity(test_text)
        
        # 验证结果
        assert isinstance(complexity_metrics, dict)
        assert "sentence_count" in complexity_metrics
        assert "word_count" in complexity_metrics
        assert "avg_sentence_length" in complexity_metrics
        assert "unique_words" in complexity_metrics
        assert "lexical_diversity" in complexity_metrics
        assert "text_length" in complexity_metrics
        
        # 验证指标值
        assert complexity_metrics["sentence_count"] > 0
        assert complexity_metrics["word_count"] > 0
        assert complexity_metrics["text_length"] > 0
    
    def test_batch_generate_summaries(self, summary_model):
        """测试批量摘要生成功能"""
        # 测试文本列表
        test_texts = [
            "文本1：这是一个测试文本。",
            "文本2：这是另一个测试文本。",
            "文本3：这是第三个测试文本。"
        ]
        
        # 批量生成摘要
        results = summary_model.batch_generate_summaries(test_texts, method="auto")
        
        # 验证结果
        assert isinstance(results, list)
        assert len(results) == len(test_texts)
        
        # 验证每个结果
        for result in results:
            assert isinstance(result, dict)
            assert "original_text" in result
            assert "summary" in result
            assert "method_used" in result
            assert "summary_length" in result
    
    def test_evaluate_summary_quality(self, summary_model):
        """测试摘要质量评估功能"""
        # 测试文本和摘要
        test_text = "这是一个测试文本，用于测试摘要质量评估功能。"
        test_summary = "测试文本摘要"
        
        # 评估摘要质量
        quality_metrics = summary_model.evaluate_summary_quality(test_text, test_summary)
        
        # 验证结果
        assert isinstance(quality_metrics, dict)
        assert "recall" in quality_metrics
        assert "precision" in quality_metrics
        assert "f1_score" in quality_metrics
        
        # 验证指标值范围
        assert 0 <= quality_metrics["recall"] <= 1
        assert 0 <= quality_metrics["precision"] <= 1
        assert 0 <= quality_metrics["f1_score"] <= 1
    
    def test_empty_text_handling(self, summary_model):
        """测试空文本处理"""
        # 测试空文本
        empty_text = ""
        summary = summary_model.select_best_summary(empty_text)
        
        # 验证结果
        assert isinstance(summary, str)
        assert summary == ""
    
    def test_none_text_handling(self, summary_model):
        """测试None文本处理"""
        # 测试None文本
        summary = summary_model.select_best_summary(None)
        
        # 验证结果
        assert isinstance(summary, str)
        assert summary == ""
    
    def test_invalid_method_handling(self, summary_model):
        """测试无效方法处理"""
        # 测试无效方法
        test_text = "这是一个测试文本。"
        summary = summary_model.select_best_summary(test_text, method="invalid_method")
        
        # 验证结果 - 应该回退到auto方法
        assert isinstance(summary, str)
        assert len(summary) > 0

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__])




