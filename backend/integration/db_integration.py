"""
数据库集成服务
将NLP处理结果存储到MySQL数据库

Usage:
    from backend.integration import DatabaseIntegration
    
    db = DatabaseIntegration()
    
    # 完整的PDF处理流程
    result = db.process_and_store_pdf(
        user_id="user_001",
        file_path="/path/to/file.pdf",
        file_content=bytes_content
    )
"""

import os
import sys
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

# 添加document_system到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from document_system.services.document_service import DocumentService
from document_system.models.entity import Entity
from document_system.models.summary import Summary
from document_system.models.tag import Tag

logger = logging.getLogger(__name__)


class DatabaseIntegration:
    """
    数据库集成类
    将NLP处理结果与MySQL数据库连接
    """
    
    def __init__(self):
        """初始化数据库连接"""
        self.doc_service = DocumentService()
        self.entity_model = Entity()
        self.summary_model = Summary()
        self.tag_model = Tag()
        logger.info("数据库集成服务初始化完成")
    
    # ==================== 文档操作 ====================
    
    def create_document(
        self,
        user_id: str,
        title: str,
        file_path: str,
        file_size: int,
        **kwargs
    ) -> Dict[str, Any]:
        """
        创建文档记录
        
        Args:
            user_id: 用户ID
            title: 文档标题
            file_path: 文件存储路径
            file_size: 文件大小(字节)
            **kwargs: 其他属性(author, category, description等)
            
        Returns:
            包含doc_id的结果字典
        """
        result = self.doc_service.upload_document(
            user_id=user_id,
            title=title,
            file_path=file_path,
            file_size=file_size,
            **kwargs
        )
        
        if result.get('success'):
            logger.info(f"文档创建成功: {result.get('doc_id')}")
        else:
            logger.error(f"文档创建失败: {result.get('message')}")
        
        return result
    
    def get_document(self, doc_id: str) -> Dict[str, Any]:
        """
        获取文档完整信息(包含摘要、标签、实体)
        
        Args:
            doc_id: 文档ID
            
        Returns:
            文档信息字典
        """
        return self.doc_service.get_document_info(
            doc_id=doc_id,
            include_summary=True,
            include_tags=True,
            include_entities=True
        )
    
    # ==================== 实体操作 ====================
    
    def store_entities(
        self,
        doc_id: str,
        entities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        存储NLP识别的实体到数据库
        
        Args:
            doc_id: 文档ID
            entities: NLP识别的实体列表
                [{"text": "张三", "type": "PERSON", "confidence": 0.95, ...}]
            
        Returns:
            存储结果
        """
        if not entities:
            return {"success": True, "message": "无实体需要存储", "count": 0}
        
        # 转换格式：NLP输出 -> 数据库格式
        db_entities = []
        for entity in entities:
            db_entities.append({
                "name": entity.get("text", entity.get("name", "")),
                "type": self._map_entity_type(entity.get("type", "UNKNOWN"))
            })
        
        # 去重
        seen = set()
        unique_entities = []
        for e in db_entities:
            key = (e["name"], e["type"])
            if key not in seen:
                seen.add(key)
                unique_entities.append(e)
        
        # 批量存储
        try:
            entity_ids = self.entity_model.create_multiple_entities(doc_id, unique_entities)
            logger.info(f"成功存储 {len(entity_ids)} 个实体到文档 {doc_id}")
            return {
                "success": True,
                "message": f"成功存储 {len(entity_ids)} 个实体",
                "count": len(entity_ids),
                "entity_ids": entity_ids
            }
        except Exception as e:
            logger.error(f"存储实体失败: {e}")
            return {
                "success": False,
                "message": str(e),
                "count": 0
            }
    
    def _map_entity_type(self, nlp_type: str) -> str:
        """
        将NLP实体类型映射到数据库类型
        
        Args:
            nlp_type: NLP识别的类型(如PERSON, ORG, GPE等)
            
        Returns:
            数据库中的类型(person, organization, location等)
        """
        type_mapping = {
            # spaCy/transformers类型 -> 数据库类型
            "PERSON": "person",
            "PER": "person",
            "ORG": "organization",
            "GPE": "location",
            "LOC": "location",
            "DATE": "date",
            "TIME": "time",
            "MONEY": "money",
            "PERCENT": "percent",
            "FAC": "facility",
            "PRODUCT": "product",
            "EVENT": "event",
            "WORK_OF_ART": "work_of_art",
            "LAW": "law",
            "LANGUAGE": "language",
            "CARDINAL": "number",
            "ORDINAL": "number",
            "QUANTITY": "quantity",
            # 中文NER模型类型
            "B-PER": "person",
            "I-PER": "person",
            "B-ORG": "organization",
            "I-ORG": "organization",
            "B-LOC": "location",
            "I-LOC": "location",
        }
        return type_mapping.get(nlp_type.upper(), "other")
    
    # ==================== 摘要操作 ====================
    
    def store_summary(
        self,
        doc_id: str,
        short_summary: str = None,
        medium_summary: str = None,
        long_summary: str = None,
        method: str = "auto"
    ) -> Dict[str, Any]:
        """
        存储NLP生成的摘要到数据库
        
        Args:
            doc_id: 文档ID
            short_summary: 短摘要(约50字)
            medium_summary: 中等摘要(约150字)
            long_summary: 长摘要(约300字)
            method: 生成方法(extractive/abstractive/auto)
            
        Returns:
            存储结果
        """
        try:
            summary_id = self.summary_model.create_summary(
                doc_id=doc_id,
                short_summary=short_summary,
                medium_summary=medium_summary,
                long_summary=long_summary,
                method=method
            )
            
            if summary_id:
                logger.info(f"成功存储摘要到文档 {doc_id}")
                return {
                    "success": True,
                    "message": "摘要存储成功",
                    "summary_id": summary_id
                }
            else:
                return {
                    "success": False,
                    "message": "摘要存储失败"
                }
        except Exception as e:
            logger.error(f"存储摘要失败: {e}")
            return {
                "success": False,
                "message": str(e)
            }
    
    # ==================== 标签操作 ====================
    
    def store_tags(
        self,
        doc_id: str,
        tags: List[str],
        tag_type: str = "keyword"
    ) -> Dict[str, Any]:
        """
        存储文档标签到数据库
        
        Args:
            doc_id: 文档ID
            tags: 标签列表
            tag_type: 标签类型(keyword/category/custom)
            
        Returns:
            存储结果
        """
        if not tags:
            return {"success": True, "message": "无标签需要存储", "count": 0}
        
        try:
            tag_ids = []
            for tag_name in tags:
                tag_id = self.tag_model.create_tag(
                    doc_id=doc_id,
                    tag_name=tag_name,
                    tag_type=tag_type
                )
                if tag_id:
                    tag_ids.append(tag_id)
            
            logger.info(f"成功存储 {len(tag_ids)} 个标签到文档 {doc_id}")
            return {
                "success": True,
                "message": f"成功存储 {len(tag_ids)} 个标签",
                "count": len(tag_ids),
                "tag_ids": tag_ids
            }
        except Exception as e:
            logger.error(f"存储标签失败: {e}")
            return {
                "success": False,
                "message": str(e),
                "count": 0
            }
    
    # ==================== 完整处理流程 ====================
    
    def process_and_store_pdf(
        self,
        user_id: str,
        title: str,
        file_path: str,
        file_size: int,
        extracted_text: str,
        entities: List[Dict] = None,
        summary: Dict[str, str] = None,
        tags: List[str] = None,
        **doc_kwargs
    ) -> Dict[str, Any]:
        """
        完整的PDF处理存储流程
        
        将PDF处理的所有结果一次性存入数据库
        
        Args:
            user_id: 用户ID
            title: 文档标题
            file_path: 文件路径
            file_size: 文件大小
            extracted_text: OCR提取的文本
            entities: NLP识别的实体列表
            summary: 摘要字典 {"short": "...", "medium": "...", "long": "..."}
            tags: 标签列表
            **doc_kwargs: 其他文档属性
            
        Returns:
            完整的处理结果
        """
        result = {
            "success": False,
            "doc_id": None,
            "entities_stored": 0,
            "summary_stored": False,
            "tags_stored": 0,
            "errors": []
        }
        
        try:
            # 1. 创建文档记录
            doc_result = self.create_document(
                user_id=user_id,
                title=title,
                file_path=file_path,
                file_size=file_size,
                **doc_kwargs
            )
            
            if not doc_result.get('success'):
                result['errors'].append(f"文档创建失败: {doc_result.get('message')}")
                return result
            
            doc_id = doc_result.get('doc_id')
            result['doc_id'] = doc_id
            
            # 2. 存储实体
            if entities:
                entity_result = self.store_entities(doc_id, entities)
                result['entities_stored'] = entity_result.get('count', 0)
                if not entity_result.get('success'):
                    result['errors'].append(f"实体存储失败: {entity_result.get('message')}")
            
            # 3. 存储摘要
            if summary:
                summary_result = self.store_summary(
                    doc_id=doc_id,
                    short_summary=summary.get('short'),
                    medium_summary=summary.get('medium'),
                    long_summary=summary.get('long'),
                    method=summary.get('method', 'auto')
                )
                result['summary_stored'] = summary_result.get('success', False)
                if not summary_result.get('success'):
                    result['errors'].append(f"摘要存储失败: {summary_result.get('message')}")
            
            # 4. 存储标签
            if tags:
                tag_result = self.store_tags(doc_id, tags)
                result['tags_stored'] = tag_result.get('count', 0)
                if not tag_result.get('success'):
                    result['errors'].append(f"标签存储失败: {tag_result.get('message')}")
            
            result['success'] = len(result['errors']) == 0
            logger.info(f"PDF处理存储完成: doc_id={doc_id}, errors={len(result['errors'])}")
            
        except Exception as e:
            logger.error(f"PDF处理存储失败: {e}")
            result['errors'].append(str(e))
        
        return result
    
    # ==================== 查询操作 ====================
    
    def search_documents_by_entity(
        self,
        entity_name: str = None,
        entity_type: str = None
    ) -> List[Dict[str, Any]]:
        """
        通过实体搜索文档
        
        Args:
            entity_name: 实体名称
            entity_type: 实体类型
            
        Returns:
            匹配的文档列表
        """
        try:
            entities = self.entity_model.search_entities(
                name=entity_name,
                entity_type=entity_type
            )
            
            # 获取关联的文档信息
            doc_ids = set(e.get('doc_id') for e in entities if e.get('doc_id'))
            documents = []
            for doc_id in doc_ids:
                doc_info = self.get_document(doc_id)
                if doc_info.get('success'):
                    documents.append(doc_info.get('document'))
            
            return documents
        except Exception as e:
            logger.error(f"搜索文档失败: {e}")
            return []
    
    def get_document_statistics(self, doc_id: str) -> Dict[str, Any]:
        """
        获取文档统计信息
        
        Args:
            doc_id: 文档ID
            
        Returns:
            统计信息
        """
        doc_info = self.get_document(doc_id)
        if not doc_info.get('success'):
            return {"success": False, "message": "文档不存在"}
        
        document = doc_info.get('document', {})
        
        # 统计实体类型分布
        entities = document.get('entities', [])
        entity_type_counts = {}
        for entity in entities:
            entity_type = entity.get('type', 'unknown')
            entity_type_counts[entity_type] = entity_type_counts.get(entity_type, 0) + 1
        
        return {
            "success": True,
            "doc_id": doc_id,
            "title": document.get('title'),
            "entity_count": len(entities),
            "entity_type_distribution": entity_type_counts,
            "tag_count": len(document.get('tags', [])),
            "has_summary": document.get('summary') is not None
        }
