# -*- coding: utf-8 -*-
import mysql.connector
from mysql.connector import Error
import logging

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '12345678',
    'database': 'rjgc',
    'charset': 'utf8mb4',
    'autocommit': True
}

class DatabaseConnection:
    """数据库连接管理类"""
    
    def __init__(self):
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """建立数据库连接"""
        try:
            self.connection = mysql.connector.connect(**DB_CONFIG)
            self.cursor = self.connection.cursor(dictionary=True)
            logging.info("数据库连接成功")
            return True
        except Error as e:
            logging.error(f"数据库连接失败: {e}")
            return False
    
    def disconnect(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logging.info("数据库连接已关闭")
    
    def execute_query(self, query, params=None):
        """执行查询语句"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except Error as e:
            logging.error(f"查询执行失败: {e}")
            return None
    
    def execute_update(self, query, params=None):
        """执行更新语句(INSERT, UPDATE, DELETE)"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            self.cursor.execute(query, params)
            self.connection.commit()
            return self.cursor.lastrowid if 'INSERT' in query.upper() else self.cursor.rowcount
        except Error as e:
            logging.error(f"更新执行失败: {e}")
            if self.connection:
                self.connection.rollback()
            return None
    
    def execute_many(self, query, params_list):
        """批量执行语句"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            self.cursor.executemany(query, params_list)
            self.connection.commit()
            return self.cursor.rowcount
        except Error as e:
            logging.error(f"批量执行失败: {e}")
            if self.connection:
                self.connection.rollback()
            return None
    
    def get_connection(self):
        """获取数据库连接（用于context manager）"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connection = mysql.connector.connect(**DB_CONFIG)
            return self.connection
        except Error as e:
            logging.error(f"获取数据库连接失败: {e}")
            raise

def generate_user_id(db):
    """生成用户ID，保持user_XXX格式"""
    try:
        # 查询当前最大ID
        max_id_query = """
        SELECT MAX(user_id) as max_id 
        FROM sys_user 
        WHERE user_id REGEXP '^user_[0-9]+$'
        """
        result = db.execute_query(max_id_query)
        
        if result and result[0]['max_id']:
            # 提取数字部分并递增
            current_num = int(result[0]['max_id'].split('_')[1])
            new_num = current_num + 1
        else:
            new_num = 1
        
        return f"user_{new_num:03d}"  # 格式化为user_006
        
    except Exception as e:
        logging.error(f"生成用户ID失败: {e}")
        return None
