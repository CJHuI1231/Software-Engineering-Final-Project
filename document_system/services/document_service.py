"""
文档服务层
提供文档相关的业务逻辑
"""

from typing import Optional, List, Dict, Any
from ..models.document import Document
from ..models.summary import Summary
from ..models.tag import Tag
from ..models.entity import Entity


class DocumentService:
    """文档服务类"""
    
    def __init__(self):
        self.document_model = Document()
        self.summary_model = Summary()
        self.tag_model = Tag()
        self.entity_model = Entity()
    
    def upload_document(self, user_id: str, title: str, file_path: str, 
                        file_size: int, **kwargs) -> Dict[str, Any]:
        """
        上传文档
        
        Args:
            user_id: 用户ID
            title: 文档标题
            file_path: 文件路径
            file_size: 文件大小
            **kwargs: 其他文档属性
            
        Returns:
            上传结果
        """
        # 创建文档
        doc_id = self.document_model.create_document(
            user_id=user_id,
            title=title,
            file_path=file_path,
            file_size=file_size,
            **kwargs
        )
        
        if doc_id:
            return {
                'success': True,
                'message': '文档上传成功',
                'doc_id': doc_id
            }
        else:
            return {
                'success': False,
                'message': '文档上传失败',
                'doc_id': None
            }
    
    def get_document_info(self, doc_id: str, include_summary: bool = True,
                         include_tags: bool = True, include_entities: bool = True) -> Dict[str, Any]:
        """
        获取文档信息
        
        Args:
            doc_id: 文档ID
            include_summary: 是否包含摘要
            include_tags: 是否包含标签
            include_entities: 是否包含实体
            
        Returns:
            文档信息
        """
        # 获取基本信息
        document = self.document_model.get_document_by_id(doc_id)
        
        if not document:
            return {
                'success': False,
                'message': '文档不存在',
                'document': None
            }
        
        # 检查文档是否已删除
        if document.get('is_deleted', 0) == 1:
            return {
                'success': False,
                'message': '文档已被删除',
                'document': None
            }
        
        # 获取摘要
        summary = None
        if include_summary:
            summary = self.summary_model.get_summary_by_doc_id(doc_id)
        
        # 获取标签
        tags = []
        if include_tags:
            tags = self.tag_model.get_tags_by_doc_id(doc_id)
        
        # 获取实体
        entities = []
        if include_entities:
            entities = self.entity_model.get_entities_by_doc_id(doc_id)
        
        return {
            'success': True,
            'message': '获取文档信息成功',
            'document': {
                **document,
                'summary': summary,
                'tags': tags,
                'entities': entities
            }
        }
    
    def update_document_info(self, doc_id: str, user_id: str, **kwargs) -> Dict[str, Any]:
        """
        更新文档信息
        
        Args:
            doc_id: 文档ID
            user_id: 用户ID（用于权限验证）
            **kwargs: 要更新的字段
            
        Returns:
            更新结果
        """
        # 获取文档信息
        document = self.document_model.get_document_by_id(doc_id)
        
        if not document:
            return {
                'success': False,
                'message': '文档不存在',
                'document': None
            }
        
        # 检查权限（只有文档所有者可以更新）
        if document['user_id'] != user_id:
            return {
                'success': False,
                'message': '没有权限更新此文档',
                'document': None
            }
        
        # 更新文档信息
        success = self.document_model.update_document(doc_id, **kwargs)
        
        if success:
            updated_document = self.document_model.get_document_by_id(doc_id)
            return {
                'success': True,
                'message': '文档信息更新成功',
                'document': updated_document
            }
        else:
            return {
                'success': False,
                'message': '文档信息更新失败',
                'document': None
            }
    
    def delete_document(self, doc_id: str, user_id: str, 
                       hard_delete: bool = False) -> Dict[str, Any]:
        """
        删除文档
        
        Args:
            doc_id: 文档ID
            user_id: 用户ID（用于权限验证）
            hard_delete: 是否硬删除
            
        Returns:
            删除结果
        """
        # 获取文档信息
        document = self.document_model.get_document_by_id(doc_id)
        
        if not document:
            return {
                'success': False,
                'message': '文档不存在'
            }
        
        # 检查权限
        if document['user_id'] != user_id:
            return {
                'success': False,
                'message': '没有权限删除此文档'
            }
        
        # 执行删除
        if hard_delete:
            success = self.document_model.hard_delete_document(doc_id)
            message = '文档硬删除成功'
        else:
            success = self.document_model.soft_delete_document(doc_id)
            message = '文档软删除成功'
        
        if success:
            return {
                'success': True,
                'message': message
            }
        else:
            return {
                'success': False,
                'message': '文档删除失败'
            }
    
    def restore_document(self, doc_id: str, user_id: str) -> Dict[str, Any]:
        """
        恢复文档
        
        Args:
            doc_id: 文档ID
            user_id: 用户ID（用于权限验证）
            
        Returns:
            恢复结果
        """
        # 获取文档信息
        document = self.document_model.get_document_by_id(doc_id, include_deleted=True)
        
        if not document:
            return {
                'success': False,
                'message': '文档不存在'
            }
        
        # 检查权限
        if document['user_id'] != user_id:
            return {
                'success': False,
                'message': '没有权限恢复此文档'
            }
        
        # 检查文档是否已删除
        if document.get('is_deleted', 0) == 0:
            return {
                'success': False,
                'message': '文档未被删除，无需恢复'
            }
        
        # 恢复文档
        success = self.document_model.restore_document(doc_id)
        
        if success:
            return {
                'success': True,
                'message': '文档恢复成功'
            }
        else:
            return {
                'success': False,
                'message': '文档恢复失败'
            }
    
    def list_user_documents(self, user_id: str, include_deleted: bool = False,
                           limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        获取用户文档列表
        
        Args:
            user_id: 用户ID
            include_deleted: 是否包含已删除文档
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            文档列表
        """
        documents = self.document_model.list_user_documents(user_id, include_deleted)
        
        # 应用分页
        total = len(documents)
        paginated_docs = documents[offset:offset + limit]
        
        return {
            'success': True,
            'message': '获取文档列表成功',
            'documents': paginated_docs,
            'total': total,
            'limit': limit,
            'offset': offset
        }
    
    def search_documents(self, user_id: str, keyword: str, search_type: str = 'title',
                        limit: int = 50) -> Dict[str, Any]:
        """
        搜索文档
        
        Args:
            user_id: 用户ID
            keyword: 搜索关键词
            search_type: 搜索类型（title/author/category）
            limit: 返回数量限制
            
        Returns:
            搜索结果
        """
        documents = self.document_model.search_documents(user_id, keyword, search_type)
        
        # 手动限制结果数量
        if limit and len(documents) > limit:
            documents = documents[:limit]
        
        return {
            'success': True,
            'message': '搜索文档成功',
            'documents': documents,
            'keyword': keyword,
            'search_type': search_type,
            'total': len(documents)
        }
    
    def add_document_summary(self, doc_id: str, user_id: str, content: str,
                           length_type: str = 'medium') -> Dict[str, Any]:
        """
        添加文档摘要
        
        Args:
            doc_id: 文档ID
            user_id: 用户ID（用于权限验证）
            content: 摘要内容
            length_type: 摘要长度类型
            
        Returns:
            添加结果
        """
        # 验证文档权限
        document = self.document_model.get_document_by_id(doc_id)
        if not document:
            return {
                'success': False,
                'message': '文档不存在'
            }
        
        if document['user_id'] != user_id:
            return {
                'success': False,
                'message': '没有权限修改此文档'
            }
        
        # 创建或更新摘要
        summary_id = self.summary_model.create_summary(doc_id, content, length_type)
        
        if summary_id:
            return {
                'success': True,
                'message': '摘要添加成功',
                'summary_id': summary_id
            }
        else:
            return {
                'success': False,
                'message': '摘要添加失败'
            }
    
    def add_document_tags(self, doc_id: str, user_id: str, 
                         keywords: List[str]) -> Dict[str, Any]:
        """
        添加文档标签
        
        Args:
            doc_id: 文档ID
            user_id: 用户ID（用于权限验证）
            keywords: 关键词列表
            
        Returns:
            添加结果
        """
        # 验证文档权限
        document = self.document_model.get_document_by_id(doc_id)
        if not document:
            return {
                'success': False,
                'message': '文档不存在'
            }
        
        if document['user_id'] != user_id:
            return {
                'success': False,
                'message': '没有权限修改此文档'
            }
        
        # 批量创建标签
        tag_ids = self.tag_model.create_multiple_tags(doc_id, keywords)
        
        if tag_ids:
            return {
                'success': True,
                'message': f'成功添加 {len(tag_ids)} 个标签',
                'tag_ids': tag_ids
            }
        else:
            return {
                'success': False,
                'message': '标签添加失败'
            }
    
    def add_document_entities(self, doc_id: str, user_id: str,
                             entities: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        添加文档实体
        
        Args:
            doc_id: 文档ID
            user_id: 用户ID（用于权限验证）
            entities: 实体列表，每个实体包含name和type字段
            
        Returns:
            添加结果
        """
        # 验证文档权限
        document = self.document_model.get_document_by_id(doc_id)
        if not document:
            return {
                'success': False,
                'message': '文档不存在'
            }
        
        if document['user_id'] != user_id:
            return {
                'success': False,
                'message': '没有权限修改此文档'
            }
        
        # 批量创建实体
        entity_ids = self.entity_model.create_multiple_entities(doc_id, entities)
        
        if entity_ids:
            return {
                'success': True,
                'message': f'成功添加 {len(entity_ids)} 个实体',
                'entity_ids': entity_ids
            }
        else:
            return {
                'success': False,
                'message': '实体添加失败'
            }
    
    def get_document_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取文档统计信息
        
        Args:
            user_id: 用户ID（可选）
            
        Returns:
            统计信息
        """
        doc_stats = self.document_model.get_document_stats(user_id)
        summary_stats = self.summary_model.get_summary_stats()
        tag_stats = self.tag_model.get_tag_stats()
        entity_stats = self.entity_model.get_entity_stats()
        
        return {
            'success': True,
            'message': '获取文档统计成功',
            'stats': {
                'documents': doc_stats,
                'summaries': summary_stats,
                'tags': tag_stats,
                'entities': entity_stats
            }
        }
