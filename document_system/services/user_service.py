"""
用户服务层
提供用户相关的业务逻辑
"""

from typing import Optional, List, Dict, Any
from ..models.user import UserModel
from ..models.document import Document


class UserService:
    """用户服务类"""
    
    def __init__(self):
        self.user_model = UserModel()
        self.document_model = Document()
    
    def register_user(self, username: str, email: str, password: str, 
                      role: str = '普通用户', **kwargs) -> Dict[str, Any]:
        """
        用户注册
        
        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            role: 用户角色
            **kwargs: 其他用户属性
            
        Returns:
            注册结果
        """
        # 检查用户名是否已存在
        existing_user = self.user_model.get_user_by_username(username)
        if existing_user:
            return {
                'success': False,
                'message': '用户名已存在',
                'user_id': None
            }
        
        # 检查邮箱是否已存在
        existing_email = self.user_model.get_user_by_email(email)
        if existing_email:
            return {
                'success': False,
                'message': '邮箱已被注册',
                'user_id': None
            }
        
        # 创建用户
        user_id = self.user_model.create_user(
            username=username,
            email=email,
            password=password,
            role=role,
            **kwargs
        )
        
        if user_id:
            return {
                'success': True,
                'message': '用户注册成功',
                'user_id': user_id
            }
        else:
            return {
                'success': False,
                'message': '用户注册失败',
                'user_id': None
            }
    
    def login_user(self, username: str, password: str) -> Dict[str, Any]:
        """
        用户登录
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            登录结果
        """
        user = self.user_model.get_user_by_username(username)
        
        if not user:
            return {
                'success': False,
                'message': '用户不存在',
                'user_id': None,
                'role': None
            }
        
        if user['password'] != password:  # 实际应用中应该使用密码哈希比较
            return {
                'success': False,
                'message': '密码错误',
                'user_id': None,
                'role': None
            }
        
        if user['status'] == 0:
            return {
                'success': False,
                'message': '账号已被禁用',
                'user_id': None,
                'role': None
            }
        
        # 移除密码信息
        user.pop('password', None)
        
        return {
            'success': True,
            'message': '登录成功',
            'user_id': user['user_id'],
            'role': user['role'],
            'user': user
        }
    
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户资料
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户资料
        """
        user = self.user_model.get_user_by_id(user_id)
        
        if not user:
            return {
                'success': False,
                'message': '用户不存在',
                'profile': None
            }
        
        # 获取用户文档统计
        doc_stats = self.document_model.get_document_stats(user_id)
        
        # 移除敏感信息
        user.pop('password', None)
        
        return {
            'success': True,
            'message': '获取用户资料成功',
            'profile': {
                **user,
                'document_stats': doc_stats
            }
        }
    
    def update_user_profile(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """
        更新用户资料
        
        Args:
            user_id: 用户ID
            **kwargs: 要更新的字段
            
        Returns:
            更新结果
        """
        # 检查用户是否存在
        user = self.user_model.get_user_by_id(user_id)
        if not user:
            return {
                'success': False,
                'message': '用户不存在',
                'user': None
            }
        
        # 如果更新用户名，检查是否重复
        if 'username' in kwargs:
            existing_user = self.user_model.get_user_by_username(kwargs['username'])
            if existing_user and existing_user['user_id'] != user_id:
                return {
                    'success': False,
                    'message': '用户名已存在',
                    'user': None
                }
        
        # 如果更新邮箱，检查是否重复
        if 'email' in kwargs:
            existing_email = self.user_model.get_user_by_email(kwargs['email'])
            if existing_email and existing_email['user_id'] != user_id:
                return {
                    'success': False,
                    'message': '邮箱已被注册',
                    'user': None
                }
        
        # 更新用户信息
        success = self.user_model.update_user(user_id, **kwargs)
        
        if success:
            updated_user = self.user_model.get_user_by_id(user_id)
            updated_user.pop('password', None)
            
            return {
                'success': True,
                'message': '用户资料更新成功',
                'user': updated_user
            }
        else:
            return {
                'success': False,
                'message': '用户资料更新失败',
                'user': None
            }
    
    def change_password(self, user_id: str, old_password: str, 
                       new_password: str) -> Dict[str, Any]:
        """
        修改密码
        
        Args:
            user_id: 用户ID
            old_password: 旧密码
            new_password: 新密码
            
        Returns:
            修改结果
        """
        user = self.user_model.get_user_by_id(user_id)
        
        if not user:
            return {
                'success': False,
                'message': '用户不存在'
            }
        
        if user['password'] != old_password:  # 实际应用中应该使用密码哈希比较
            return {
                'success': False,
                'message': '原密码错误'
            }
        
        success = self.user_model.update_user(user_id, password=new_password)
        
        if success:
            return {
                'success': True,
                'message': '密码修改成功'
            }
        else:
            return {
                'success': False,
                'message': '密码修改失败'
            }
    
    def deactivate_user(self, user_id: str) -> Dict[str, Any]:
        """
        禁用用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            禁用结果
        """
        user = self.user_model.get_user_by_id(user_id)
        
        if not user:
            return {
                'success': False,
                'message': '用户不存在'
            }
        
        if user['status'] == 0:
            return {
                'success': False,
                'message': '用户已被禁用'
            }
        
        success = self.user_model.update_user(user_id, status=0)
        
        if success:
            return {
                'success': True,
                'message': '用户禁用成功'
            }
        else:
            return {
                'success': False,
                'message': '用户禁用失败'
            }
    
    def activate_user(self, user_id: str) -> Dict[str, Any]:
        """
        激活用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            激活结果
        """
        user = self.user_model.get_user_by_id(user_id)
        
        if not user:
            return {
                'success': False,
                'message': '用户不存在'
            }
        
        if user['status'] == 1:
            return {
                'success': False,
                'message': '用户已激活'
            }
        
        success = self.user_model.update_user(user_id, status=1)
        
        if success:
            return {
                'success': True,
                'message': '用户激活成功'
            }
        else:
            return {
                'success': False,
                'message': '用户激活失败'
            }
    
    def list_users(self, role: Optional[str] = None, status: Optional[int] = None,
                   limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        获取用户列表
        
        Args:
            role: 角色过滤（可选）
            status: 状态过滤（可选）
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            用户列表
        """
        users = self.user_model.list_users(role, status, limit, offset)
        
        # 移除密码信息
        for user in users:
            user.pop('password', None)
        
        return {
            'success': True,
            'message': '获取用户列表成功',
            'users': users,
            'total': len(users)
        }
    
    def get_user_stats(self) -> Dict[str, Any]:
        """
        获取用户统计信息
        
        Returns:
            用户统计信息
        """
        stats = self.user_model.get_user_stats()
        
        return {
            'success': True,
            'message': '获取用户统计成功',
            'stats': stats
        }
    
    def set_user_status(self, user_id: str, status: int) -> Dict[str, Any]:
        """
        设置用户状态
        
        Args:
            user_id: 用户ID
            status: 状态（0-禁用，1-激活）
            
        Returns:
            设置结果
        """
        user = self.user_model.get_user_by_id(user_id)
        
        if not user:
            return {
                'success': False,
                'message': '用户不存在'
            }
        
        success = self.user_model.update_user(user_id, status=status)
        
        if success:
            status_text = "激活" if status == 1 else "禁用"
            return {
                'success': True,
                'message': f'用户{status_text}成功'
            }
        else:
            return {
                'success': False,
                'message': '用户状态设置失败'
            }
    
    def get_users_list(self, role: Optional[str] = None, limit: int = 50, 
                      offset: int = 0) -> Dict[str, Any]:
        """
        获取用户列表（兼容方法）
        
        Args:
            role: 角色过滤（可选）
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            用户列表
        """
        return self.list_users(role=role, limit=limit, offset=offset)
    
    def get_users_statistics(self) -> Dict[str, Any]:
        """
        获取用户统计信息（兼容方法）
        
        Returns:
            用户统计信息
        """
        result = self.get_user_stats()
        if result['success']:
            return {
                'success': True,
                'statistics': result['stats']
            }
        else:
            return {
                'success': False,
                'statistics': {}
            }
