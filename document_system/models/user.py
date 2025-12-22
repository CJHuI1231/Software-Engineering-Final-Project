# -*- coding: utf-8 -*-
"""
用户模型
"""

import logging
from ..config.database import DatabaseConnection, generate_user_id

class UserModel:
    """用户数据模型"""
    
    def __init__(self):
        self.db = DatabaseConnection()
    
    def create_user(self, username, email, password, role='普通用户', status=1, theme='light', summary_length='medium', **kwargs):
        """创建用户"""
        try:
            # 验证参数
            valid_roles = ['普通用户', '科研人员', '教师', '管理员']
            valid_status = [0, 1]
            valid_themes = ['light', 'dark']
            valid_summary_lengths = ['short', 'medium', 'long']
            
            if role not in valid_roles:
                return None
            
            if status not in valid_status:
                return None
            
            if theme not in valid_themes:
                return None
            
            if summary_length not in valid_summary_lengths:
                return None
            
            # 生成用户ID
            user_id = generate_user_id(self.db)
            if not user_id:
                return None
            
            # 插入用户
            with self.db.get_connection() as connection:
                with connection.cursor() as cursor:
                    # 检查邮箱和用户名是否已存在
                    check_query = "SELECT user_id FROM sys_user WHERE username = %s OR email = %s"
                    cursor.execute(check_query, (username, email))
                    if cursor.fetchone():
                        return None
                    
                    insert_query = """
                    INSERT INTO sys_user (user_id, username, email, password, role, status, theme, summary_length, create_time, update_time) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    """
                    cursor.execute(insert_query, (user_id, username, email, password, role, status, theme, summary_length))
                    connection.commit()
                    return user_id
                
        except Exception as e:
            logging.error(f"创建用户失败: {e}")
            return None
    
    def get_user_by_id(self, user_id):
        """根据ID获取用户"""
        try:
            with self.db.get_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    query = "SELECT * FROM sys_user WHERE user_id = %s"
                    cursor.execute(query, (user_id,))
                    result = cursor.fetchone()
                    return result
            
        except Exception as e:
            logging.error(f"获取用户失败: {e}")
            return None
    
    def get_user_by_email(self, email):
        """根据邮箱获取用户"""
        try:
            with self.db.get_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    query = "SELECT * FROM sys_user WHERE email = %s"
                    cursor.execute(query, (email,))
                    result = cursor.fetchone()
                    return result
            
        except Exception as e:
            logging.error(f"获取用户失败: {e}")
            return None
    
    def get_user_by_username(self, username):
        """根据用户名获取用户"""
        try:
            with self.db.get_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    query = "SELECT * FROM sys_user WHERE username = %s"
                    cursor.execute(query, (username,))
                    result = cursor.fetchone()
                    return result
            
        except Exception as e:
            logging.error(f"获取用户失败: {e}")
            return None
    
    def list_users(self, role=None, status=None, limit=None, offset=None):
        """获取用户列表"""
        try:
            with self.db.get_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    query = "SELECT * FROM sys_user WHERE 1=1"
                    params = []
                    
                    if role:
                        query += " AND role = %s"
                        params.append(role)
                    
                    if status is not None:
                        query += " AND status = %s"
                        params.append(status)
                    
                    query += " ORDER BY user_id"
                    
                    if offset:
                        query += " OFFSET %s"
                        params.append(offset)
                    
                    if limit:
                        query += " LIMIT %s"
                        params.append(limit)
                    
                    cursor.execute(query, params)
                    result = cursor.fetchall()
                    return result or []
            
        except Exception as e:
            logging.error(f"获取用户列表失败: {e}")
            return []
    
    def update_user(self, user_id, **kwargs):
        """更新用户信息"""
        try:
            # 验证参数
            valid_roles = ['普通用户', '科研人员', '教师', '管理员']
            valid_status = [0, 1]
            valid_themes = ['light', 'dark']
            valid_summary_lengths = ['short', 'medium', 'long']
            
            if 'role' in kwargs and kwargs['role'] not in valid_roles:
                return False
            
            if 'status' in kwargs and kwargs['status'] not in valid_status:
                return False
            
            if 'theme' in kwargs and kwargs['theme'] not in valid_themes:
                return False
            
            if 'summary_length' in kwargs and kwargs['summary_length'] not in valid_summary_lengths:
                return False
            
            with self.db.get_connection() as connection:
                with connection.cursor() as cursor:
                    # 检查用户是否存在
                    check_query = "SELECT user_id FROM sys_user WHERE user_id = %s"
                    cursor.execute(check_query, (user_id,))
                    if not cursor.fetchone():
                        return False
                    
                    # 构建更新语句
                    update_fields = []
                    params = []
                    
                    for field, value in kwargs.items():
                        if field in ['username', 'email', 'password', 'role', 'status', 'theme', 'summary_length']:
                            update_fields.append(f"{field} = %s")
                            params.append(value)
                    
                    if not update_fields:
                        return False
                    
                    query = f"UPDATE sys_user SET {', '.join(update_fields)} WHERE user_id = %s"
                    params.append(user_id)
                    
                    cursor.execute(query, params)
                    connection.commit()
                    return cursor.rowcount > 0
                
        except Exception as e:
            logging.error(f"更新用户失败: {e}")
            return False
    
    def delete_user(self, user_id):
        """删除用户（级联删除相关数据）"""
        try:
            with self.db.get_connection() as connection:
                with connection.cursor() as cursor:
                    # 检查用户是否存在
                    check_query = "SELECT user_id FROM sys_user WHERE user_id = %s"
                    cursor.execute(check_query, (user_id,))
                    if not cursor.fetchone():
                        return False
                    
                    query = "DELETE FROM sys_user WHERE user_id = %s"
                    cursor.execute(query, (user_id,))
                    connection.commit()
                    return cursor.rowcount > 0
                
        except Exception as e:
            logging.error(f"删除用户失败: {e}")
            return False
    
    def get_user_stats(self):
        """获取用户统计信息"""
        try:
            with self.db.get_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    query = """
                    SELECT 
                        COUNT(*) as total_users,
                        COUNT(CASE WHEN status = 1 THEN 1 END) as active_users,
                        COUNT(CASE WHEN status = 0 THEN 1 END) as inactive_users,
                        COUNT(CASE WHEN role = '普通用户' THEN 1 END) as regular_users,
                        COUNT(CASE WHEN role = '科研人员' THEN 1 END) as researchers,
                        COUNT(CASE WHEN role = '教师' THEN 1 END) as teachers,
                        COUNT(CASE WHEN role = '管理员' THEN 1 END) as admins
                    FROM sys_user
                    """
                    cursor.execute(query)
                    result = cursor.fetchone()
                    return result
            
        except Exception as e:
            logging.error(f"获取用户统计失败: {e}")
            return {}
