"""
命令行解析器
提供统一的命令行接口
"""

import argparse
import sys
from typing import Dict, Any, List
from .services.user_service import UserService
from .services.document_service import DocumentService


class CLIParser:
    """命令行解析器类"""
    
    def __init__(self):
        self.user_service = UserService()
        self.document_service = DocumentService()
        self.parser = None
        self._setup_parser()
    
    def _setup_parser(self):
        """设置命令行解析器"""
        self.parser = argparse.ArgumentParser(
            description='文档管理系统命令行工具',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # 创建子命令解析器
        subparsers = self.parser.add_subparsers(dest='command', help='可用命令')
        
        # 用户相关命令
        self._setup_user_commands(subparsers)
        
        # 文档相关命令
        self._setup_document_commands(subparsers)
        
        # 摘要相关命令
        self._setup_summary_commands(subparsers)
        
        # 标签相关命令
        self._setup_tag_commands(subparsers)
        
        # 实体相关命令
        self._setup_entity_commands(subparsers)
        
        # 导出相关命令
        self._setup_export_commands(subparsers)
    
    def _setup_user_commands(self, subparsers):
        """设置用户相关命令"""
        # 用户注册
        register_parser = subparsers.add_parser('user-register', help='用户注册')
        register_parser.add_argument('--username', required=True, help='用户名')
        register_parser.add_argument('--email', required=True, help='邮箱')
        register_parser.add_argument('--password', required=True, help='密码')
        register_parser.add_argument('--role', default='普通用户', help='用户角色')
        
        # 用户登录
        login_parser = subparsers.add_parser('user-login', help='用户登录')
        login_parser.add_argument('--email', required=True, help='邮箱')
        login_parser.add_argument('--password', required=True, help='密码')
        
        # 获取用户资料
        profile_parser = subparsers.add_parser('user-profile', help='获取用户资料')
        profile_parser.add_argument('--user-id', required=True, help='用户ID')
        
        # 更新用户资料
        update_parser = subparsers.add_parser('user-update', help='更新用户资料')
        update_parser.add_argument('--user-id', required=True, help='用户ID')
        update_parser.add_argument('--username', help='新用户名')
        update_parser.add_argument('--email', help='新邮箱')
        update_parser.add_argument('--role', help='新角色')
        update_parser.add_argument('--theme', help='界面主题')
        update_parser.add_argument('--summary-length', help='摘要长度偏好')
        
        # 修改密码
        password_parser = subparsers.add_parser('user-password', help='修改密码')
        password_parser.add_argument('--user-id', required=True, help='用户ID')
        password_parser.add_argument('--old-password', required=True, help='旧密码')
        password_parser.add_argument('--new-password', required=True, help='新密码')
        
        # 用户列表
        list_parser = subparsers.add_parser('user-list', help='获取用户列表')
        list_parser.add_argument('--role', help='角色过滤')
        list_parser.add_argument('--status', type=int, help='状态过滤')
        list_parser.add_argument('--limit', type=int, default=50, help='返回数量限制')
        list_parser.add_argument('--offset', type=int, default=0, help='偏移量')
        
        # 用户统计
        stats_parser = subparsers.add_parser('user-stats', help='获取用户统计')
    
    def _setup_document_commands(self, subparsers):
        """设置文档相关命令"""
        # 上传文档
        upload_parser = subparsers.add_parser('doc-upload', help='上传文档')
        upload_parser.add_argument('--user-id', required=True, help='用户ID')
        upload_parser.add_argument('--title', required=True, help='文档标题')
        upload_parser.add_argument('--file-path', required=True, help='文件路径')
        upload_parser.add_argument('--file-size', type=int, required=True, help='文件大小')
        upload_parser.add_argument('--author', help='作者')
        upload_parser.add_argument('--file-format', default='pdf', help='文件格式')
        upload_parser.add_argument('--category', help='文档分类')
        
        # 获取文档信息
        info_parser = subparsers.add_parser('doc-info', help='获取文档信息')
        info_parser.add_argument('--doc-id', required=True, help='文档ID')
        info_parser.add_argument('--no-summary', action='store_true', help='不包含摘要')
        info_parser.add_argument('--no-tags', action='store_true', help='不包含标签')
        info_parser.add_argument('--no-entities', action='store_true', help='不包含实体')
        
        # 更新文档信息
        update_parser = subparsers.add_parser('doc-update', help='更新文档信息')
        update_parser.add_argument('--doc-id', required=True, help='文档ID')
        update_parser.add_argument('--user-id', required=True, help='用户ID')
        update_parser.add_argument('--title', help='新标题')
        update_parser.add_argument('--author', help='新作者')
        update_parser.add_argument('--category', help='新分类')
        
        # 删除文档
        delete_parser = subparsers.add_parser('doc-delete', help='删除文档')
        delete_parser.add_argument('--doc-id', required=True, help='文档ID')
        delete_parser.add_argument('--user-id', required=True, help='用户ID')
        delete_parser.add_argument('--hard', action='store_true', help='硬删除')
        
        # 恢复文档
        restore_parser = subparsers.add_parser('doc-restore', help='恢复文档')
        restore_parser.add_argument('--doc-id', required=True, help='文档ID')
        restore_parser.add_argument('--user-id', required=True, help='用户ID')
        
        # 文档列表
        list_parser = subparsers.add_parser('doc-list', help='获取文档列表')
        list_parser.add_argument('--user-id', required=True, help='用户ID')
        list_parser.add_argument('--include-deleted', action='store_true', help='包含已删除文档')
        list_parser.add_argument('--limit', type=int, default=50, help='返回数量限制')
        list_parser.add_argument('--offset', type=int, default=0, help='偏移量')
        
        # 搜索文档
        search_parser = subparsers.add_parser('doc-search', help='搜索文档')
        search_parser.add_argument('--user-id', required=True, help='用户ID')
        search_parser.add_argument('--keyword', required=True, help='搜索关键词')
        search_parser.add_argument('--type', choices=['title', 'author', 'category'], 
                                  default='title', help='搜索类型')
        search_parser.add_argument('--limit', type=int, default=50, help='返回数量限制')
        
        # 文档统计
        stats_parser = subparsers.add_parser('doc-stats', help='获取文档统计')
        stats_parser.add_argument('--user-id', help='用户ID（可选）')
    
    def _setup_summary_commands(self, subparsers):
        """设置摘要相关命令"""
        # 添加摘要
        add_parser = subparsers.add_parser('summary-add', help='添加文档摘要')
        add_parser.add_argument('--doc-id', required=True, help='文档ID')
        add_parser.add_argument('--user-id', required=True, help='用户ID')
        add_parser.add_argument('--content', required=True, help='摘要内容')
        add_parser.add_argument('--type', choices=['short', 'medium', 'long'],
                               default='medium', help='摘要长度类型')
        
        # 获取摘要
        get_parser = subparsers.add_parser('summary-get', help='获取文档摘要')
        get_parser.add_argument('--doc-id', required=True, help='文档ID')
        
        # 更新摘要
        update_parser = subparsers.add_parser('summary-update', help='更新文档摘要')
        update_parser.add_argument('--doc-id', required=True, help='文档ID')
        update_parser.add_argument('--content', help='新摘要内容')
        update_parser.add_argument('--type', choices=['short', 'medium', 'long'],
                                  help='新摘要长度类型')
    
    def _setup_tag_commands(self, subparsers):
        """设置标签相关命令"""
        # 添加标签
        add_parser = subparsers.add_parser('tag-add', help='添加文档标签')
        add_parser.add_argument('--doc-id', required=True, help='文档ID')
        add_parser.add_argument('--user-id', required=True, help='用户ID')
        add_parser.add_argument('--keywords', nargs='+', required=True, help='关键词列表')
        
        # 获取标签
        get_parser = subparsers.add_parser('tag-get', help='获取文档标签')
        get_parser.add_argument('--doc-id', required=True, help='文档ID')
        
        # 根据标签搜索文档
        search_parser = subparsers.add_parser('tag-search', help='根据标签搜索文档')
        search_parser.add_argument('--keywords', nargs='+', required=True, help='关键词列表')
        search_parser.add_argument('--match', choices=['any', 'all'], default='any',
                                  help='匹配类型')
        search_parser.add_argument('--limit', type=int, default=50, help='返回数量限制')
        
        # 热门标签
        popular_parser = subparsers.add_parser('tag-popular', help='获取热门标签')
        popular_parser.add_argument('--limit', type=int, default=20, help='返回数量限制')
    
    def _setup_entity_commands(self, subparsers):
        """设置实体相关命令"""
        # 添加实体
        add_parser = subparsers.add_parser('entity-add', help='添加文档实体')
        add_parser.add_argument('--doc-id', required=True, help='文档ID')
        add_parser.add_argument('--user-id', required=True, help='用户ID')
        add_parser.add_argument('--entities', nargs='+', required=True, 
                               help='实体列表，格式：name:type name:type')
        
        # 获取实体
        get_parser = subparsers.add_parser('entity-get', help='获取文档实体')
        get_parser.add_argument('--doc-id', required=True, help='文档ID')
        
        # 根据实体搜索文档
        search_parser = subparsers.add_parser('entity-search', help='根据实体搜索文档')
        search_parser.add_argument('--names', nargs='+', required=True, help='实体名称列表')
        search_parser.add_argument('--match', choices=['any', 'all'], default='any',
                                   help='匹配类型')
        search_parser.add_argument('--limit', type=int, default=50, help='返回数量限制')
        
        # 热门实体
        popular_parser = subparsers.add_parser('entity-popular', help='获取热门实体')
        popular_parser.add_argument('--type', help='实体类型过滤')
        popular_parser.add_argument('--limit', type=int, default=20, help='返回数量限制')
    
    def _setup_export_commands(self, subparsers):
        """设置导出相关命令"""
        # 创建导出任务
        create_parser = subparsers.add_parser('export-create', help='创建导出任务')
        create_parser.add_argument('--user-id', required=True, help='用户ID')
        create_parser.add_argument('--type', choices=['graph', 'summary', 'document', 'tags'],
                                   required=True, help='导出类型')
        create_parser.add_argument('--format', choices=['png', 'jpg', 'pdf', 'html', 'json'],
                                   required=True, help='导出格式')
        create_parser.add_argument('--doc-ids', nargs='+', help='关联文档ID列表')
        
        # 获取导出任务
        get_parser = subparsers.add_parser('export-get', help='获取导出任务')
        get_parser.add_argument('--export-id', required=True, help='导出ID')
        
        # 导出任务列表
        list_parser = subparsers.add_parser('export-list', help='获取导出任务列表')
        list_parser.add_argument('--user-id', required=True, help='用户ID')
        list_parser.add_argument('--status', choices=['pending', 'processing', 'completed', 'failed'],
                                help='状态过滤')
        list_parser.add_argument('--limit', type=int, default=50, help='返回数量限制')
        
        # 导出统计
        stats_parser = subparsers.add_parser('export-stats', help='获取导出统计')
        stats_parser.add_argument('--user-id', help='用户ID（可选）')
    
    def parse_and_execute(self, args: List[str] = None) -> Dict[str, Any]:
        """
        解析命令行参数并执行对应操作
        
        Args:
            args: 命令行参数列表，如果为None则使用sys.argv
            
        Returns:
            执行结果
        """
        if args is None:
            args = sys.argv[1:]
        
        if not args:
            self.parser.print_help()
            return {'success': False, 'message': '请提供命令'}
        
        try:
            parsed_args = self.parser.parse_args(args)
            return self._execute_command(parsed_args)
        except Exception as e:
            return {'success': False, 'message': f'命令执行失败: {str(e)}'}
    
    def _execute_command(self, args) -> Dict[str, Any]:
        """执行对应的命令"""
        command = args.command
        
        if command.startswith('user-'):
            return self._execute_user_command(command, args)
        elif command.startswith('doc-'):
            return self._execute_document_command(command, args)
        elif command.startswith('summary-'):
            return self._execute_summary_command(command, args)
        elif command.startswith('tag-'):
            return self._execute_tag_command(command, args)
        elif command.startswith('entity-'):
            return self._execute_entity_command(command, args)
        elif command.startswith('export-'):
            return self._execute_export_command(command, args)
        else:
            return {'success': False, 'message': f'未知命令: {command}'}
    
    def _execute_user_command(self, command: str, args) -> Dict[str, Any]:
        """执行用户相关命令"""
        if command == 'user-register':
            return self.user_service.register_user(
                username=args.username,
                email=args.email,
                password=args.password,
                role=args.role
            )
        elif command == 'user-login':
            return self.user_service.login_user(
                email=args.email,
                password=args.password
            )
        elif command == 'user-profile':
            return self.user_service.get_user_profile(args.user_id)
        elif command == 'user-update':
            kwargs = {}
            if args.username: kwargs['username'] = args.username
            if args.email: kwargs['email'] = args.email
            if args.role: kwargs['role'] = args.role
            if args.theme: kwargs['theme'] = args.theme
            if args.summary_length: kwargs['summary_length'] = args.summary_length
            
            return self.user_service.update_user_profile(args.user_id, **kwargs)
        elif command == 'user-password':
            return self.user_service.change_password(
                user_id=args.user_id,
                old_password=args.old_password,
                new_password=args.new_password
            )
        elif command == 'user-list':
            return self.user_service.list_users(
                role=args.role,
                status=args.status,
                limit=args.limit,
                offset=args.offset
            )
        elif command == 'user-stats':
            return self.user_service.get_user_stats()
    
    def _execute_document_command(self, command: str, args) -> Dict[str, Any]:
        """执行文档相关命令"""
        if command == 'doc-upload':
            kwargs = {}
            if args.author: kwargs['author'] = args.author
            if args.category: kwargs['category'] = args.category
            
            return self.document_service.upload_document(
                user_id=args.user_id,
                title=args.title,
                file_path=args.file_path,
                file_size=args.file_size,
                file_format=args.file_format,
                **kwargs
            )
        elif command == 'doc-info':
            return self.document_service.get_document_info(
                doc_id=args.doc_id,
                include_summary=not args.no_summary,
                include_tags=not args.no_tags,
                include_entities=not args.no_entities
            )
        elif command == 'doc-update':
            kwargs = {}
            if args.title: kwargs['title'] = args.title
            if args.author: kwargs['author'] = args.author
            if args.category: kwargs['category'] = args.category
            
            return self.document_service.update_document_info(
                doc_id=args.doc_id,
                user_id=args.user_id,
                **kwargs
            )
        elif command == 'doc-delete':
            return self.document_service.delete_document(
                doc_id=args.doc_id,
                user_id=args.user_id,
                hard_delete=args.hard
            )
        elif command == 'doc-restore':
            return self.document_service.restore_document(
                doc_id=args.doc_id,
                user_id=args.user_id
            )
        elif command == 'doc-list':
            return self.document_service.list_user_documents(
                user_id=args.user_id,
                include_deleted=args.include_deleted,
                limit=args.limit,
                offset=args.offset
            )
        elif command == 'doc-search':
            return self.document_service.search_documents(
                user_id=args.user_id,
                keyword=args.keyword,
                search_type=args.type,
                limit=args.limit
            )
        elif command == 'doc-stats':
            return self.document_service.get_document_stats(user_id=args.user_id)
    
    def _execute_summary_command(self, command: str, args) -> Dict[str, Any]:
        """执行摘要相关命令"""
        if command == 'summary-add':
            return self.document_service.add_document_summary(
                doc_id=args.doc_id,
                user_id=args.user_id,
                content=args.content,
                length_type=args.type
            )
        elif command == 'summary-get':
            doc_info = self.document_service.get_document_info(
                doc_id=args.doc_id,
                include_summary=True,
                include_tags=False,
                include_entities=False
            )
            if doc_info['success']:
                return {
                    'success': True,
                    'message': '获取摘要成功',
                    'summary': doc_info['document'].get('summary')
                }
            else:
                return doc_info
        elif command == 'summary-update':
            from .models.summary import Summary
            summary_model = Summary()
            
            kwargs = {}
            if args.content: kwargs['content'] = args.content
            if args.type: kwargs['length_type'] = args.type
            
            success = summary_model.update_summary(args.doc_id, **kwargs)
            return {
                'success': success,
                'message': '摘要更新成功' if success else '摘要更新失败'
            }
    
    def _execute_tag_command(self, command: str, args) -> Dict[str, Any]:
        """执行标签相关命令"""
        if command == 'tag-add':
            return self.document_service.add_document_tags(
                doc_id=args.doc_id,
                user_id=args.user_id,
                keywords=args.keywords
            )
        elif command == 'tag-get':
            doc_info = self.document_service.get_document_info(
                doc_id=args.doc_id,
                include_summary=False,
                include_tags=True,
                include_entities=False
            )
            if doc_info['success']:
                return {
                    'success': True,
                    'message': '获取标签成功',
                    'tags': doc_info['document'].get('tags', [])
                }
            else:
                return doc_info
        elif command == 'tag-search':
            from .models.tag import Tag
            tag_model = Tag()
            
            documents = tag_model.search_documents_by_keywords(
                keywords=args.keywords,
                match_type=args.match,
                limit=args.limit
            )
            return {
                'success': True,
                'message': '搜索文档成功',
                'documents': documents,
                'keywords': args.keywords,
                'match_type': args.match,
                'total': len(documents)
            }
        elif command == 'tag-popular':
            from .models.tag import Tag
            tag_model = Tag()
            
            keywords = tag_model.get_popular_keywords(limit=args.limit)
            return {
                'success': True,
                'message': '获取热门标签成功',
                'keywords': keywords
            }
    
    def _execute_entity_command(self, command: str, args) -> Dict[str, Any]:
        """执行实体相关命令"""
        if command == 'entity-add':
            # 解析实体列表：name:type name:type
            entities = []
            for entity_str in args.entities:
                if ':' in entity_str:
                    name, entity_type = entity_str.split(':', 1)
                    entities.append({'name': name, 'type': entity_type})
            
            return self.document_service.add_document_entities(
                doc_id=args.doc_id,
                user_id=args.user_id,
                entities=entities
            )
        elif command == 'entity-get':
            doc_info = self.document_service.get_document_info(
                doc_id=args.doc_id,
                include_summary=False,
                include_tags=False,
                include_entities=True
            )
            if doc_info['success']:
                return {
                    'success': True,
                    'message': '获取实体成功',
                    'entities': doc_info['document'].get('entities', [])
                }
            else:
                return doc_info
        elif command == 'entity-search':
            from .models.entity import Entity
            entity_model = Entity()
            
            documents = entity_model.search_documents_by_entities(
                entity_names=args.names,
                match_type=args.match,
                limit=args.limit
            )
            return {
                'success': True,
                'message': '搜索文档成功',
                'documents': documents,
                'entity_names': args.names,
                'match_type': args.match,
                'total': len(documents)
            }
        elif command == 'entity-popular':
            from .models.entity import Entity
            entity_model = Entity()
            
            entities = entity_model.get_popular_entities(
                entity_type=args.type,
                limit=args.limit
            )
            return {
                'success': True,
                'message': '获取热门实体成功',
                'entities': entities
            }
    
    def _execute_export_command(self, command: str, args) -> Dict[str, Any]:
        """执行导出相关命令"""
        from .models.export import Export
        export_model = Export()
        
        if command == 'export-create':
            export_params = {}
            if args.doc_ids:
                export_params['doc_ids'] = args.doc_ids
            
            export_id = export_model.create_export(
                user_id=args.user_id,
                export_type=args.type,
                format=args.format,
                doc_ids=args.doc_ids,
                export_params=export_params
            )
            
            if export_id:
                return {
                    'success': True,
                    'message': '导出任务创建成功',
                    'export_id': export_id
                }
            else:
                return {
                    'success': False,
                    'message': '导出任务创建失败'
                }
        elif command == 'export-get':
            export_info = export_model.get_export_by_id(args.export_id)
            if export_info:
                return {
                    'success': True,
                    'message': '获取导出任务成功',
                    'export': export_info
                }
            else:
                return {
                    'success': False,
                    'message': '导出任务不存在'
                }
        elif command == 'export-list':
            exports = export_model.list_user_exports(
                user_id=args.user_id,
                status=args.status,
                limit=args.limit
            )
            return {
                'success': True,
                'message': '获取导出任务列表成功',
                'exports': exports,
                'total': len(exports)
            }
        elif command == 'export-stats':
            stats = export_model.get_export_stats(user_id=args.user_id)
            return {
                'success': True,
                'message': '获取导出统计成功',
                'stats': stats
            }
