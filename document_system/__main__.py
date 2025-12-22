#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档系统主入口模块
提供统一的接口来使用文档系统的所有功能
"""

from .services.user_service import UserService
from .services.document_service import DocumentService
from .models.tag import Tag
from .models.user import UserModel
from .models.document import Document
from .models.entity import Entity
from .models.summary import Summary
from .models.export import Export
from .config.database import DatabaseConnection


class DocumentSystem:
    """文档系统主类，提供所有功能的统一访问接口"""
    
    def __init__(self, db_config=None):
        """
        初始化文档系统
        
        Args:
            db_config: 数据库配置字典，如果为None则使用默认配置
        """
        # 初始化数据库连接
        if db_config:
            self.db = DatabaseConnection(**db_config)
        else:
            self.db = DatabaseConnection()
        
        # 初始化服务层
        self.user_service = UserService()
        self.document_service = DocumentService()
        
        # 初始化模型层
        self.user_model = UserModel()
        self.document_model = Document()
        self.tag_model = Tag()
        self.entity_model = Entity()
        self.summary_model = Summary()
        self.export_model = Export()
    
    # 用户相关功能
    def register_user(self, username, email, password, **kwargs):
        """用户注册"""
        return self.user_service.register_user(username, email, password, **kwargs)
    
    def login_user(self, username, password):
        """用户登录"""
        return self.user_service.login_user(username, password)
    
    def get_user_profile(self, user_id):
        """获取用户资料"""
        return self.user_service.get_user_profile(user_id)
    
    def update_user_profile(self, user_id, **kwargs):
        """更新用户资料"""
        return self.user_service.update_user_profile(user_id, **kwargs)
    
    def change_password(self, user_id, old_password, new_password):
        """修改密码"""
        return self.user_service.change_password(user_id, old_password, new_password)
    
    # 文档相关功能
    def upload_document(self, user_id, title, author, file_path, **kwargs):
        """上传文档"""
        return self.document_service.upload_document(user_id, title, author, file_path, **kwargs)
    
    def get_document_info(self, doc_id):
        """获取文档信息"""
        return self.document_service.get_document_info(doc_id)
    
    def update_document(self, doc_id, **kwargs):
        """更新文档信息"""
        return self.document_service.update_document_info(doc_id, **kwargs)
    
    def delete_document(self, doc_id):
        """删除文档"""
        return self.document_service.delete_document(doc_id)
    
    def list_user_documents(self, user_id, **kwargs):
        """列出用户文档"""
        return self.document_service.list_user_documents(user_id, **kwargs)
    
    def search_documents(self, **kwargs):
        """搜索文档"""
        return self.document_service.search_documents(**kwargs)
    
    # 标签相关功能
    def create_tag(self, doc_id, keyword, synonyms=None):
        """创建标签"""
        return self.tag_model.create_tag(doc_id, keyword, synonyms)
    
    def get_document_tags(self, doc_id):
        """获取文档标签"""
        return self.tag_model.get_tags_by_doc_id(doc_id)
    
    def search_documents_by_keywords(self, keywords, match_type='any', limit=50):
        """根据关键词搜索文档"""
        return self.tag_model.search_documents_by_keywords(keywords, match_type, limit)
    
    def get_popular_keywords(self, limit=20):
        """获取热门关键词"""
        return self.tag_model.get_popular_keywords(limit)
    
    # 实体识别相关功能
    def get_document_entities(self, doc_id):
        """获取文档实体"""
        return self.entity_model.get_entities_by_doc_id(doc_id)
    
    # 摘要相关功能
    def get_document_summary(self, doc_id):
        """获取文档摘要"""
        return self.summary_model.get_summary_by_doc_id(doc_id)
    
    # 统计相关功能
    def get_user_stats(self):
        """获取用户统计"""
        return self.user_service.get_users_statistics()
    
    def get_document_stats(self, user_id=None):
        """获取文档统计"""
        return self.document_service.get_document_stats(user_id)
    
    def get_tag_stats(self):
        """获取标签统计"""
        return self.tag_model.get_tag_stats()
    
    def close(self):
        """关闭数据库连接"""
        # 数据库连接使用上下文管理器，无需手动关闭
        pass


# 便捷函数
def create_document_system(db_config=None):
    """创建文档系统实例"""
    return DocumentSystem(db_config)


def main():
    """命令行入口"""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='文档系统命令行工具')
    parser.add_argument('--config', type=str, help='数据库配置文件路径')
    parser.add_argument('--test', action='store_true', help='运行测试')
    
    args = parser.parse_args()
    
    # 加载配置
    db_config = None
    if args.config:
        with open(args.config, 'r', encoding='utf-8') as f:
            db_config = json.load(f)
    
    # 创建系统实例
    system = create_document_system(db_config)
    
    if args.test:
        # 运行基本测试
        print("文档系统测试")
        print(f"数据库连接: {'成功' if system.db else '失败'}")
        print("所有模块加载完成")
    else:
        print("文档系统已启动")
        print("使用 --help 查看帮助信息")
    
    system.close()


if __name__ == '__main__':
    main()
