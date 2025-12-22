# 文档智能分析系统

一个基于Python和MySQL的智能文档管理系统，提供完整的文档存储、智能检索、摘要生成、标签管理、实体识别和导出功能。

## ✨ 功能特性

### 🔐 用户管理
- 用户注册、登录、资料管理
- 角色权限控制（普通用户、科研人员、教师、管理员）
- 用户状态管理（激活/禁用）
- 密码修改和安全验证

### 📄 文档管理
- 文档上传和信息管理
- 文档分类和元数据管理
- 智能搜索（标题、作者、分类、关键词）
- 软删除和硬删除
- 文档恢复功能

### 🧠 智能内容处理
- 自动摘要生成（短/中/长三种长度）
- 文档标签管理和关键词提取
- 命名实体识别和分类
- 内容分析和统计

### 📤 导出功能
- 多种导出格式（PNG、JPG、PDF、HTML、JSON）
- 导出任务管理
- 导出历史记录
- 下载统计

### 📊 数据统计
- 用户活动统计
- 文档使用统计
- 标签和实体分析
- 导出统计报告

## 🏗️ 系统架构

```
document_system/
├── __init__.py           # 模块入口，导出主要接口
├── __main__.py          # 主入口，统一DocumentSystem类
├── config/              # 配置模块
│   └── database.py      # 数据库配置和连接管理
├── models/              # 数据模型层
│   ├── __init__.py
│   ├── user.py          # 用户模型
│   ├── document.py      # 文档模型
│   ├── summary.py       # 摘要模型
│   ├── tag.py           # 标签模型
│   ├── entity.py        # 实体模型
│   └── export.py        # 导出模型
├── services/            # 业务逻辑层
│   ├── user_service.py  # 用户服务
│   └── document_service.py # 文档服务
└── utils/               # 工具函数
```

## 🚀 快速开始

### 1. 环境要求
- Python 3.8+
- MySQL 5.7+ 或 8.0+
- mysql-connector-python

### 2. 安装依赖
```bash
pip install mysql-connector-python python-dotenv
```

### 3. 数据库配置

#### 方法一：使用配置文件
创建 `config.json`：
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

### 4. 初始化数据库
```sql
-- 创建数据库
CREATE DATABASE document_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 执行建表脚本
mysql -u username -p document_system < ForCreate_Improved.sql
```

## 💻 使用方法

### Python API 使用（推荐）

#### 基本使用
```python
from document_system import create_document_system

# 创建系统实例
system = create_document_system()

try:
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
            
            # 上传文档
            doc_result = system.upload_document(
                user_id=user_id,
                title='测试文档',
                author='测试作者',
                file_path='/path/to/document.pdf',
                file_size=1024,
                file_format='PDF',
                category='技术文档'
            )
            
            if doc_result['success']:
                doc_id = doc_result['doc_id']
                print(f"文档上传成功，ID: {doc_id}")
                
                # 添加标签
                tag_result = system.create_tag(doc_id, 'Python编程', 'Python, 编程')
                if tag_result:
                    print("标签添加成功")
                
                # 获取文档信息
                doc_info = system.get_document_info(doc_id)
                if doc_info['success']:
                    document = doc_info['document']
                    print(f"标题: {document['title']}")
                    print(f"作者: {document['author']}")
finally:
    system.close()
```

#### 高级功能示例
```python
# 搜索文档
search_result = system.search_documents(
    user_id=user_id,
    keyword='Python',
    search_type='title'
)

# 标签搜索
tag_search = system.search_documents_by_keywords(
    keywords=['Python', '机器学习'],
    match_type='any',
    limit=10
)

# 获取热门关键词
popular_keywords = system.get_popular_keywords(limit=20)

# 获取统计信息
user_stats = system.get_user_stats()
doc_stats = system.get_document_stats(user_id)
tag_stats = system.get_tag_stats()
```

### 命令行使用

#### 测试系统
```bash
# 基本测试
python -m document_system --test

# 使用自定义配置
python -m document_system --config config.json
```

#### 传统命令行接口（已弃用，建议使用Python API）
```bash
# 用户注册
python main.py user-register --username "张三" --email "zhangsan@example.com" --password "123456"

# 文档上传
python main.py doc-upload --user-id "user_001" --title "机器学习导论" --file-path "/path/to/doc.pdf"
```

## 📚 API 文档

### 🔐 用户管理 API

#### `register_user(username, email, password, **kwargs)`
用户注册
- **参数**: username, email, password, real_name(可选), role(可选)
- **返回**: `{'success': bool, 'message': str, 'user_id': str | None}`

#### `login_user(username, password)`
用户登录
- **参数**: username, password
- **返回**: `{'success': bool, 'message': str, 'user_id': str | None, 'role': str | None}`

#### `get_user_profile(user_id)`
获取用户资料
- **参数**: user_id
- **返回**: `{'success': bool, 'message': str, 'user': dict | None}`

#### `update_user_profile(user_id, **kwargs)`
更新用户资料
- **参数**: user_id, real_name(可选), theme(可选), 等
- **返回**: `{'success': bool, 'message': str}`

#### `change_password(user_id, old_password, new_password)`
修改密码
- **参数**: user_id, old_password, new_password
- **返回**: `{'success': bool, 'message': str}`

### 📄 文档管理 API

#### `upload_document(user_id, title, author, file_path, **kwargs)`
上传文档
- **参数**: user_id, title, author, file_path, file_size, file_format(可选), category(可选)
- **返回**: `{'success': bool, 'message': str, 'doc_id': str | None}`

#### `get_document_info(doc_id)`
获取文档信息
- **参数**: doc_id
- **返回**: `{'success': bool, 'message': str, 'document': dict | None}`

#### `update_document(doc_id, **kwargs)`
更新文档信息
- **参数**: doc_id, title(可选), author(可选), category(可选), 等
- **返回**: `{'success': bool, 'message': str}`

#### `delete_document(doc_id)`
删除文档
- **参数**: doc_id
- **返回**: `{'success': bool, 'message': str}`

#### `list_user_documents(user_id, **kwargs)`
列出用户文档
- **参数**: user_id, include_deleted(可选), limit(可选), offset(可选)
- **返回**: `{'success': bool, 'message': str, 'documents': list | None}`

#### `search_documents(**kwargs)`
搜索文档
- **参数**: user_id, keyword, search_type, limit(可选)
- **返回**: `{'success': bool, 'message': str, 'documents': list | None}`

### 🏷️ 标签管理 API

#### `create_tag(doc_id, keyword, synonyms=None)`
创建标签
- **参数**: doc_id, keyword, synonyms(可选)
- **返回**: tag_id 或 None

#### `get_document_tags(doc_id)`
获取文档标签
- **参数**: doc_id
- **返回**: 标签列表

#### `search_documents_by_keywords(keywords, match_type='any', limit=50)`
根据关键词搜索文档
- **参数**: keywords, match_type, limit
- **返回**: 文档列表

#### `get_popular_keywords(limit=20)`
获取热门关键词
- **参数**: limit
- **返回**: 热门关键词列表

### 📊 统计信息 API

#### `get_user_stats()`
获取用户统计
- **返回**: `{'success': bool, 'message': str, 'statistics': dict | None}`

#### `get_document_stats(user_id=None)`
获取文档统计
- **参数**: user_id(可选)
- **返回**: `{'success': bool, 'message': str, 'statistics': dict | None}`

#### `get_tag_stats()`
获取标签统计
- **返回**: 统计信息字典

## 🗄️ 数据库设计

### 核心表结构

#### 用户表 (sys_user)
- user_id: 用户唯一标识（user_001格式）
- username: 用户名
- email: 邮箱
- password: 密码
- role: 用户角色
- status: 账号状态
- theme: 界面主题
- summary_length: 摘要长度偏好

#### 文档表 (doc_document)
- doc_id: 文档唯一标识（doc_001格式）
- user_id: 所属用户ID
- title: 文档标题
- author: 文档作者
- file_path: 文件路径
- file_size: 文件大小
- file_format: 文件格式
- category: 文档分类
- is_deleted: 逻辑删除标记

#### 摘要表 (doc_summary)
- summary_id: 摘要唯一标识（sum_001格式）
- doc_id: 关联文档ID
- content: 摘要内容
- length_type: 摘要长度类型

#### 标签表 (doc_tag)
- tag_id: 标签唯一标识（tag_001格式）
- doc_id: 关联文档ID
- keyword: 标签关键词
- synonyms: 同义词

#### 实体表 (doc_entity)
- entity_id: 实体唯一标识（ent_001格式）
- doc_id: 关联文档ID
- name: 实体名称
- type: 实体类型

#### 导出表 (doc_export)
- export_id: 导出唯一标识（exp_001格式）
- user_id: 用户ID
- export_type: 导出类型
- format: 导出格式
- doc_ids: 关联文档ID列表
- status: 导出状态

## 🎯 特性说明

### 1. 统一接口设计
- 通过 `DocumentSystem` 类提供统一的功能访问
- 支持依赖注入和配置管理
- 简化的API调用方式

### 2. 级联更新和删除
系统实现了完整的数据库级联关系：
- 用户删除时，相关文档、摘要、标签、实体、导出记录自动删除
- 文档删除时，相关摘要、标签、实体自动删除
- 用户ID修改时，相关记录自动更新

### 3. ID生成策略
- 用户ID: user_001, user_002, ...
- 文档ID: doc_001, doc_002, ...
- 摘要ID: sum_001, sum_002, ...
- 标签ID: tag_001, tag_002, ...
- 实体ID: ent_001, ent_002, ...
- 导出ID: exp_001, exp_002, ...

### 4. 权限控制
- 用户只能操作自己的文档
- 管理员可以操作所有用户的文档
- 支持角色级别的权限控制

### 5. 数据完整性
- 外键约束确保数据一致性
- 触发器自动维护元数据
- 事务处理确保操作原子性

## 🔧 配置选项

### 数据库配置
```python
db_config = {
    'host': 'localhost',
    'user': 'your_username',
    'password': 'your_password',
    'database': 'document_system',
    'port': 3306,
    'charset': 'utf8mb4'
}
```

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

## 🧪 测试

### 基本测试
```bash
python -m document_system --test
```

### 完整功能测试
参考 `DOCUMENT_SYSTEM_GUIDE.md` 中的测试示例

## ❓ 常见问题

### Q1: 数据库连接失败怎么办？
**A:** 检查以下几点：
1. 确认数据库服务已启动
2. 检查配置文件中的连接参数
3. 确认数据库用户权限
4. 检查防火墙设置

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

## 📖 详细文档

更多详细使用说明请参考：
- [DOCUMENT_SYSTEM_GUIDE.md](./DOCUMENT_SYSTEM_GUIDE.md) - 完整使用指南
- [数据库部署指南.md](./数据库部署指南.md) - 数据库部署说明

## 📄 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 邮箱: 2081237669@qq.com
- GitHub: https://github.com/asfwfdsa

document-management-system
