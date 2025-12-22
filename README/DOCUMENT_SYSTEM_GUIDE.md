# 文档系统使用指南

## 📋 目录

1. [系统概述](#系统概述)
2. [环境配置](#环境配置)
3. [安装指南](#安装指南)
4. [快速开始](#快速开始)
5. [API 文档](#api-文档)
6. [使用示例](#使用示例)
7. [配置说明](#配置说明)
8. [常见问题](#常见问题)
9. [最佳实践](#最佳实践)

---

## 🎯 系统概述

文档系统是一个完整的文档管理解决方案，提供以下核心功能：

### 🔧 核心模块

- **用户管理**: 用户注册、登录、权限管理
- **文档管理**: 文档上传、检索、更新、删除
- **标签系统**: 文档标签、关键词搜索
- **实体识别**: 自动提取文档中的命名实体
- **摘要生成**: 自动生成文档摘要
- **导出功能**: 支持多种格式导出

### 🏗️ 架构设计

```
document_system/
├── config/          # 数据库配置
├── models/          # 数据模型层
├── services/        # 业务逻辑层
├── utils/           # 工具函数
└── __main__.py      # 主入口模块
```

---

## 🛠️ 环境配置

### 系统要求

- **Python**: 3.8+
- **数据库**: MySQL 5.7+ 或 MariaDB 10.3+
- **操作系统**: Windows/Linux/macOS

### 依赖包

```bash
pip install mysql-connector-python
pip install python-dotenv
```

### 数据库准备

1. 创建数据库：
```sql
CREATE DATABASE document_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. 创建用户（可选）：
```sql
CREATE USER 'docuser'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON document_system.* TO 'docuser'@'localhost';
FLUSH PRIVILEGES;
```

---

## 📦 安装指南

### 1. 克隆项目

```bash
git clone <repository-url>
cd Software-Engineering-Final-Project
```

### 2. 配置数据库

#### 方法一：使用配置文件

创建 `config.json` 文件：

```json
{
    "host": "localhost",
    "user": "your_username",
    "password": "your_password",
    "database": "document_system",
    "port": 3306,
    "charset": "utf8mb4"
}
```

#### 方法二：环境变量

创建 `.env` 文件：

```env
DB_HOST=localhost
DB_USER=your_username
DB_PASSWORD=your_password
DB_DATABASE=document_system
DB_PORT=3306
DB_CHARSET=utf8mb4
```

### 3. 初始化数据库

```sql
-- 运行数据库初始化脚本
source ForCreate_Improved.sql;
```

---

## 🚀 快速开始

### 基本使用

```python
from document_system import create_document_system

# 创建系统实例
system = create_document_system()

# 用户注册
result = system.register_user(
    username='testuser',
    email='test@example.com',
    password='password123',
    real_name='测试用户'
)

if result['success']:
    user_id = result['user_id']
    print(f"用户注册成功，ID: {user_id}")
    
    # 用户登录
    login_result = system.login_user('testuser', 'password123')
    if login_result['success']:
        print("登录成功")

# 关闭系统
system.close()
```

### 命令行使用

```bash
# 测试系统
python -m document_system --test

# 使用自定义配置
python -m document_system --config config.json
```

---

## 📚 API 文档

### 🔐 用户管理 API

#### 用户注册

```python
register_user(username, email, password, **kwargs)
```

**参数:**
- `username`: 用户名 (必填)
- `email`: 邮箱 (必填)
- `password`: 密码 (必填)
- `real_name`: 真实姓名 (可选)
- `role`: 用户角色 (可选，默认: '普通用户')

**返回:**
```python
{
    'success': bool,
    'message': str,
    'user_id': str | None
}
```

#### 用户登录

```python
login_user(username, password)
```

**参数:**
- `username`: 用户名
- `password`: 密码

**返回:**
```python
{
    'success': bool,
    'message': str,
    'user_id': str | None,
    'role': str | None,
    'user': dict | None
}
```

#### 获取用户资料

```python
get_user_profile(user_id)
```

#### 更新用户资料

```python
update_user_profile(user_id, **kwargs)
```

#### 修改密码

```python
change_password(user_id, old_password, new_password)
```

---

### 📄 文档管理 API

#### 上传文档

```python
upload_document(user_id, title, author, file_path, **kwargs)
```

**参数:**
- `user_id`: 用户ID
- `title`: 文档标题
- `author`: 作者
- `file_path`: 文件路径
- `file_size`: 文件大小 (必填)
- `file_format`: 文件格式 (可选)
- `category`: 文档分类 (可选)

**返回:**
```python
{
    'success': bool,
    'message': str,
    'doc_id': str | None
}
```

#### 获取文档信息

```python
get_document_info(doc_id, include_summary=True, include_tags=True, include_entities=True)
```

#### 更新文档信息

```python
update_document(doc_id, user_id, **kwargs)
```

#### 删除文档

```python
delete_document(doc_id, user_id, hard_delete=False)
```

#### 列出用户文档

```python
list_user_documents(user_id, include_deleted=False, limit=50, offset=0)
```

#### 搜索文档

```python
search_documents(user_id, keyword, search_type='title', limit=50)
```

---

### 🏷️ 标签管理 API

#### 创建标签

```python
create_tag(doc_id, keyword, synonyms=None)
```

#### 获取文档标签

```python
get_document_tags(doc_id)
```

#### 根据关键词搜索文档

```python
search_documents_by_keywords(keywords, match_type='any', limit=50)
```

#### 获取热门关键词

```python
get_popular_keywords(limit=20)
```

---

### 🏷️ 实体识别 API

#### 获取文档实体

```python
get_document_entities(doc_id)
```

---

### 📝 摘要管理 API

#### 获取文档摘要

```python
get_document_summary(doc_id)
```

---

### 📊 统计信息 API

#### 获取用户统计

```python
get_user_stats()
```

#### 获取文档统计

```python
get_document_stats(user_id=None)
```

#### 获取标签统计

```python
get_tag_stats()
```

---

## 💡 使用示例

### 完整的用户文档管理流程

```python
from document_system import create_document_system

def demo_document_management():
    # 初始化系统
    system = create_document_system()
    
    try:
        # 1. 用户注册
        print("=== 用户注册 ===")
        register_result = system.register_user(
            username='demo_user',
            email='demo@example.com',
            password='demo123',
            real_name='演示用户'
        )
        
        if not register_result['success']:
            print(f"注册失败: {register_result['message']}")
            return
        
        user_id = register_result['user_id']
        print(f"用户注册成功，ID: {user_id}")
        
        # 2. 用户登录
        print("\n=== 用户登录 ===")
        login_result = system.login_user('demo_user', 'demo123')
        if not login_result['success']:
            print(f"登录失败: {login_result['message']}")
            return
        
        print(f"登录成功，角色: {login_result['role']}")
        
        # 3. 上传文档
        print("\n=== 上传文档 ===")
        upload_result = system.upload_document(
            user_id=user_id,
            title='测试文档',
            author='演示作者',
            file_path='/path/to/document.pdf',
            file_size=1024,
            file_format='PDF',
            category='技术文档'
        )
        
        if not upload_result['success']:
            print(f"上传失败: {upload_result['message']}")
            return
        
        doc_id = upload_result['doc_id']
        print(f"文档上传成功，ID: {doc_id}")
        
        # 4. 添加标签
        print("\n=== 添加标签 ===")
        tag_result = system.create_tag(doc_id, 'Python编程', 'Python, 编程')
        if tag_result:
            print("标签添加成功")
        
        # 5. 获取文档信息
        print("\n=== 获取文档信息 ===")
        doc_info = system.get_document_info(doc_id)
        if doc_info['success']:
            document = doc_info['document']
            print(f"标题: {document['title']}")
            print(f"作者: {document['author']}")
            print(f"标签数量: {len(document['tags'])}")
        
        # 6. 搜索文档
        print("\n=== 搜索文档 ===")
        search_result = system.search_documents(
            user_id=user_id,
            keyword='测试',
            search_type='title'
        )
        
        if search_result['success']:
            print(f"找到 {len(search_result['documents'])} 个相关文档")
        
        # 7. 获取统计信息
        print("\n=== 统计信息 ===")
        user_stats = system.get_user_stats()
        if user_stats['success']:
            stats = user_stats['statistics']
            print(f"总用户数: {stats.get('total_users', 0)}")
            print(f"活跃用户数: {stats.get('active_users', 0)}")
        
    finally:
        system.close()

if __name__ == '__main__':
    demo_document_management()
```

### 标签搜索示例

```python
def demo_tag_search():
    system = create_document_system()
    
    try:
        # 搜索包含特定关键词的文档
        keywords = ['Python', '机器学习', '数据分析']
        
        # 匹配任意关键词
        result_any = system.search_documents_by_keywords(
            keywords=keywords,
            match_type='any',
            limit=10
        )
        
        print(f"匹配任意关键词的文档: {len(result_any)} 个")
        
        # 匹配所有关键词
        result_all = system.search_documents_by_keywords(
            keywords=keywords,
            match_type='all',
            limit=10
        )
        
        print(f"匹配所有关键词的文档: {len(result_all)} 个")
        
        # 获取热门关键词
        popular = system.get_popular_keywords(limit=10)
        print("热门关键词:")
        for keyword in popular:
            print(f"  - {keyword['keyword']}: {keyword['usage_count']} 次")
    
    finally:
        system.close()
```

---

## ⚙️ 配置说明

### 数据库配置选项

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `host` | str | localhost | 数据库主机地址 |
| `user` | str | root | 数据库用户名 |
| `password` | str | | 数据库密码 |
| `database` | str | document_system | 数据库名称 |
| `port` | int | 3306 | 数据库端口 |
| `charset` | str | utf8mb4 | 字符集 |

### 用户角色说明

| 角色 | 权限 |
|------|------|
| 普通用户 | 管理自己的文档 |
| 科研人员 | 普通用户权限 + 高级搜索 |
| 教师 | 普通用户权限 + 批量操作 |
| 管理员 | 所有权限 |

### 摘要长度类型

| 类型 | 说明 |
|------|------|
| short | 短摘要 (50-100字) |
| medium | 中等摘要 (100-200字) |
| long | 长摘要 (200-300字) |

---

## ❓ 常见问题

### Q1: 数据库连接失败怎么办？

**A:** 检查以下几点：
1. 确认数据库服务已启动
2. 检查配置文件中的连接参数
3. 确认数据库用户权限
4. 检查防火墙设置

```python
# 测试数据库连接
from document_system.config.database import DatabaseConnection

try:
    db = DatabaseConnection()
    with db.get_connection() as conn:
        print("数据库连接成功")
except Exception as e:
    print(f"连接失败: {e}")
```

### Q2: 如何处理大文件上传？

**A:** 建议以下做法：
1. 使用分块上传
2. 增加数据库 `max_allowed_packet` 设置
3. 考虑使用文件存储服务

### Q3: 如何备份和恢复数据？

**A:** 备份策略：
```bash
# 备份数据库
mysqldump -u username -p document_system > backup.sql

# 恢复数据库
mysql -u username -p document_system < backup.sql
```

### Q4: 如何优化搜索性能？

**A:** 优化建议：
1. 为搜索字段添加索引
2. 使用全文索引
3. 实现缓存机制
4. 分页查询结果

### Q5: 如何扩展系统功能？

**A:** 扩展方式：
1. 继承现有模型类
2. 添加新的服务层
3. 实现插件机制
4. 使用装饰器模式

---

## 🎯 最佳实践

### 1. 错误处理

```python
def safe_operation():
    system = create_document_system()
    try:
        result = system.register_user('test', 'test@example.com', 'pass')
        if not result['success']:
            # 记录错误日志
            logging.error(f"注册失败: {result['message']}")
            return False
        
        # 处理成功情况
        user_id = result['user_id']
        # ... 其他操作
        
    except Exception as e:
        logging.error(f"操作异常: {e}")
        return False
    finally:
        system.close()
```

### 2. 连接池管理

```python
# 使用上下文管理器确保连接正确关闭
with create_document_system() as system:
    # 执行操作
    result = system.login_user('user', 'pass')
    # 连接会自动关闭
```

### 3. 配置管理

```python
import os
from document_system import create_document_system

# 从环境变量加载配置
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_DATABASE', 'document_system')
}

system = create_document_system(db_config)
```

### 4. 日志记录

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('document_system')

# 使用日志
logger.info("用户登录成功")
logger.error("数据库连接失败")
```

### 5. 性能优化

```python
# 批量操作
def batch_create_tags(system, doc_id, keywords):
    """批量创建标签"""
    for keyword in keywords:
        result = system.create_tag(doc_id, keyword)
        if not result['success']:
            logger.warning(f"标签创建失败: {keyword}")

# 分页查询
def list_documents_with_pagination(system, user_id, page_size=20):
    """分页获取文档列表"""
    page = 0
    while True:
        result = system.list_user_documents(
            user_id=user_id,
            limit=page_size,
            offset=page * page_size
        )
        
        if not result['success'] or not result['documents']:
            break
        
        for doc in result['documents']:
            yield doc
        
        page += 1
```

---

## 📞 技术支持

如果在使用过程中遇到问题，请：

1. 查看日志文件
2. 检查配置文件
3. 参考本文档的常见问题部分
4. 提交 Issue 到项目仓库

---

## 📄 许可证

本项目采用 MIT 许可证，详情请参阅 LICENSE 文件。

---

*最后更新: 2025年12月*
