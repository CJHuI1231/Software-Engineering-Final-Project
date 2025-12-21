import spacy
from typing import List, Dict, Any
from transformers import pipeline
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EntityRecognitionModel:
    def __init__(self):
        """初始化实体识别模型"""
        try:
            # 加载spaCy的预训练模型
            self.nlp = spacy.load("zh_core_web_sm")
            logger.info("成功加载spaCy中文模型")
            
            # 加载Hugging Face的transformers管道
            self.transformer_pipeline = pipeline(
                "ner", 
                model="ckiplab/bert-base-chinese-ner", # 原来的不能识别中文
                aggregation_strategy="simple"
            )
            logger.info("成功加载transformers NER模型")
            
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise RuntimeError(f"无法加载实体识别模型: {e}")
    
    def recognize_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        识别文本中的实体
        
        Args:
            text: 需要识别实体的文本
            
        Returns:
            包含实体信息的列表
        """
        if not text or not isinstance(text, str):
            return []
        
        try:
            # 使用spaCy进行实体识别
            doc = self.nlp(text)
            
            entities = []
            for ent in doc.ents:
                entities.append({
                    "text": ent.text,
                    "type": ent.label_,
                    "start_pos": ent.start_char,
                    "end_pos": ent.end_char,
                    "confidence": 0.9  # spaCy不提供置信度，使用默认值
                })
            
            logger.info(f"使用spaCy识别到 {len(entities)} 个实体")
            return entities
            
        except Exception as e:
            logger.error(f"spaCy实体识别失败: {e}")
            return []
    
    def recognize_entities_with_transformers(self, text: str) -> List[Dict[str, Any]]:
        """
        使用transformers进行实体识别
        
        Args:
            text: 需要识别实体的文本
            
        Returns:
            包含实体信息的列表
        """
        if not text or not isinstance(text, str):
            return []
        
        try:
            # 使用transformers管道进行实体识别
            results = self.transformer_pipeline(text)
            
            entities = []
            for result in results:
                entities.append({
                    "text": result["word"],
                    "type": result["entity_group"],
                    "start_pos": result["start"],
                    "end_pos": result["end"],
                    "confidence": result["score"]
                })
            
            logger.info(f"使用transformers识别到 {len(entities)} 个实体")
            return entities
            
        except Exception as e:
            logger.error(f"transformers实体识别失败: {e}")
            return []
    
    def classify_entities(self, entities: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
        """
        对实体进行分类
        
        Args:
            entities: 实体列表
            
        Returns:
            按类型分类的实体字典
        """
        if not entities:
            return {}
        
        classified_entities = {}
        
        for entity in entities:
            entity_type = entity.get("type", "UNKNOWN")
            if entity_type not in classified_entities:
                classified_entities[entity_type] = []
            classified_entities[entity_type].append(entity)
        
        logger.info(f"实体分类完成，共 {len(classified_entities)} 种类型")
        return classified_entities
    
    def extract_entity_relations(self, text: str) -> List[Dict[str, Any]]:
        """
        提取实体间的关系（简化版）
        
        Args:
            text: 需要分析实体关系的文本
            
        Returns:
            实体关系列表
        """
        if not text or not isinstance(text, str):
            return []
        
        try:
            # 使用spaCy的依存解析来提取关系
            doc = self.nlp(text)
            relations = []

            # 改进关系提取逻辑
            for sentence in doc.sents:
                for token in sentence:
                    if token.pos_ == "VERB":
                        subject = None
                        object_ = None
                        relation = token.text

                        for child in token.children:
                            if child.dep_ in ["nsubj", "nsubjpass"]:
                                subject = child.text
                            elif child.dep_ in ["dobj", "pobj", "attr"]:
                                object_ = child.text
                        
                        if not object_:
                            # 尝试从介词短语中寻找宾语
                            for prep in token.children:
                                if prep.dep_ == "prep":
                                    for pobj in prep.children:
                                        if pobj.dep_ == "pobj":
                                            object_ = pobj.text
                                            relation = f"{token.text}{prep.text}"
                                            break
                                        
                        if subject and object_:
                            relations.append({
                                "subject": subject,
                                "relation": relation,
                                "object": object_,
                                "confidence": 0.8  # 简化版，使用默认置信度
                            })

            # 备用简单关系提取逻辑
            if not relations:
                entities = [entity for entity in doc.ents]
                for i, entity1 in enumerate(entities):
                    for entity2 in entities[i+1:]:

                        start = min(entity1.end, entity2.end)
                        end = max(entity1.start, entity2.start)
                        span = doc[start:end]
                        verbs = [token for token in span if token.pos_ == "VERB"]

                        if verbs:
                            relations.append({
                                "subject": entity1.text,
                                "relation": verbs[0].text,
                                "object": entity2.text,
                                "confidence": 0.5  # 简化版，使用较低置信度
                            })
            
            logger.info(f"提取到 {len(relations)} 个实体关系")
            return relations
            
        except Exception as e:
            logger.error(f"实体关系提取失败: {e}")
            return []
    
    def analyze_text_with_llm(self, text: str, task: str = "entity_recognition") -> Dict[str, Any]:
        """
        使用LLM进行文本分析
        
        Args:
            text: 需要分析的文本
            task: 分析任务类型
            
        Returns:
            分析结果
        """
        if not text or not isinstance(text, str):
            return {}
        
        try:
            # 这里可以使用任何LLM服务，例如OpenAI、本地模型等
            # 示例使用Hugging Face的pipeline作为简化版
            if task == "entity_recognition":
                entities = self.recognize_entities_with_transformers(text)
                return {
                    "status": "success",
                    "entities": entities,
                    "method_used": "transformers_ner"
                }
            elif task == "summary":
                # 简化的摘要生成（实际应用中应使用专门的摘要模型）
                summary = self._generate_simple_summary(text)
                return {
                    "status": "success",
                    "summary": summary,
                    "method_used": "simple_summary"
                }
            else:
                return {"status": "error", "message": "不支持的任务类型"}
                
        except Exception as e:
            logger.error(f"LLM分析失败: {e}")
            return {"status": "error", "message": str(e)}
    
    def _generate_simple_summary(self, text: str, max_length: int = 100) -> str:
        """
        简化的摘要生成方法（用于演示）
        
        Args:
            text: 原始文本
            max_length: 摘要最大长度
            
        Returns:
            生成的摘要
        """
        if not text or not isinstance(text, str):
            return ""
        
        # 简单的摘要生成逻辑：取前max_length个字符
        return text[:max_length] + "..." if len(text) > max_length else text
    
    def batch_process(self, texts: List[str], task: str = "entity_recognition") -> List[Dict[str, Any]]:
        """
        批量处理文本
        
        Args:
            texts: 文本列表
            task: 处理任务
            
        Returns:
            处理结果列表
        """
        if not texts or not isinstance(texts, list):
            return []
        
        results = []
        for text in texts:
            result = self.analyze_text_with_llm(text, task)
            results.append(result)
        
        return results
    
    def get_supported_entity_types(self) -> List[str]:
        """
        获取支持的实体类型
        
        Returns:
            实体类型列表
        """
        return ["PERSON", "ORG", "GPE", "LOC", "DATE", "TIME", "MONEY", "PERCENT", "FAC", "PRODUCT", "EVENT", "WORK_OF_ART", "LAW", "LANGUAGE", "DATE", "CARDINAL", "ORDINAL", "QUANTITY"]
