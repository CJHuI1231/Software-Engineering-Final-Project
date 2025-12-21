# Graph Storage 模块

Neo4j 图数据库集成模块，用于存储通过 NLP 检索到的命名实体与其关系。

## 目录

- [功能特性](#功能特性)
- [模块结构](#模块结构)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [API 参考](#api-参考)
- [与 NLP 模块集成](#与-nlp-模块集成)
- [数据模型](#数据模型)
- [部署指南](#部署指南)

---

## 功能特性

- ✅ **Neo4j 连接管理**：单例模式、连接池、健康检查
- ✅ **实体存储**：支持 17 种实体类型的 CRUD 操作
- ✅ **关系存储**：支持 25+ 种关系类型的 CRUD 操作
- ✅ **批量操作**：高效的批量创建和删除
- ✅ **智能去重**：自动识别并合并重复实体/关系
- ✅ **NLP 集成**：无缝对接 NLP 模块的实体识别输出
- ✅ **RESTful API**：完整的 FastAPI 接口
- ✅ **图查询**：邻域查询、路径查找、图数据导出
- ✅ **Docker 支持**：一键部署 Neo4j 服务
- ✅ **可视化预留**：图数据格式兼容主流可视化库

---

## 模块结构

```
graph_storage/
├── __init__.py              # 模块入口，导出所有公开 API
├── main.py                  # FastAPI 应用入口
├── neo4j_connector.py       # Neo4j 连接管理器
├── README.md                # 本文档
│
├── api/                     # API 接口层
│   ├── __init__.py
│   └── graph_api.py         # RESTful API 路由定义
│
├── models/                  # 数据模型层
│   ├── __init__.py
│   ├── entity_model.py      # 实体数据模型
│   └── relation_model.py    # 关系数据模型
│
├── storage/                 # 存储操作层
│   ├── __init__.py
│   ├── entity_storage.py    # 实体 CRUD 操作
│   ├── relation_storage.py  # 关系 CRUD 操作
│   └── graph_storage.py     # 高级图操作
│
├── utils/                   # 工具模块
│   ├── __init__.py
│   ├── config.py            # 配置管理
│   └── errors.py            # 异常定义
│
├── integration/             # 集成模块
│   ├── __init__.py
│   └── nlp_integration.py   # NLP 模块集成服务
│
└── tests/                   # 测试模块
    ├── __init__.py
    └── test_models.py       # 单元测试
```

---

## 快速开始

### 1. 安装依赖

```bash
pip install neo4j
```

或使用项目的 requirements.txt：

```bash
pip install -r requirements.txt
```

### 2. 启动 Neo4j 服务

**方式 A：使用 Docker（推荐）**

```bash
cd backend
docker-compose up -d neo4j
```

**方式 B：手动安装**

1. 下载 [Neo4j Community Edition](https://neo4j.com/download/)
2. 启动服务，默认端口：
   - HTTP: `7474`
   - Bolt: `7687`

### 3. 连接数据库

```python
from backend.graph_storage import connect_neo4j

# 连接到 Neo4j
connector = connect_neo4j(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password123"
)

# 检查连接状态
print(connector.health_check())
```

### 4. 存储 NLP 结果

```python
from backend.graph_storage import store_nlp_results

# NLP 模块输出的实体和关系
entities = [
    {"text": "张三", "type": "PERSON", "confidence": 0.95},
    {"text": "阿里巴巴", "type": "ORG", "confidence": 0.92}
]

relations = [
    {"subject": "张三", "relation": "works_at", "object": "阿里巴巴", "confidence": 0.85}
]

# 存储到图数据库
result = store_nlp_results(
    entities=entities,
    relations=relations,
    source_document="document_001.pdf"
)

print(result)
# {'entities_created': 2, 'relations_created': 1, ...}
```

---

## 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j 连接 URI |
| `NEO4J_USER` | `neo4j` | 用户名 |
| `NEO4J_PASSWORD` | `password` | 密码 |
| `NEO4J_DATABASE` | `neo4j` | 数据库名 |
| `GRAPH_AUTO_CONNECT` | `false` | 启动时自动连接 |
| `GRAPH_LOG_LEVEL` | `INFO` | 日志级别 |

### 配置文件

在 `deployment_config.yaml` 中配置：

```yaml
graph_storage:
  neo4j:
    uri: "bolt://localhost:7687"
    user: "neo4j"
    password: "password123"
    database: "neo4j"
    max_connection_pool_size: 50
    connection_timeout: 30.0
  auto_connect: false
  create_indexes_on_startup: true
```

### 代码配置

```python
from backend.graph_storage.utils import GraphConfig, load_config

# 从文件加载
config = load_config("path/to/config.yaml")

# 或手动创建
config = GraphConfig()
config.neo4j.uri = "bolt://localhost:7687"
config.neo4j.password = "your_password"
```

---

## API 参考

### 基础端点

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/graph/connect` | 连接到 Neo4j |
| GET | `/graph/health` | 健康检查 |
| POST | `/graph/disconnect` | 断开连接 |

### 实体操作

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/graph/entities` | 创建实体 |
| POST | `/graph/entities/batch` | 批量创建实体 |
| GET | `/graph/entities` | 获取实体列表 |
| GET | `/graph/entities/{id}` | 获取单个实体 |
| PUT | `/graph/entities/{id}` | 更新实体 |
| DELETE | `/graph/entities/{id}` | 删除实体 |

### 关系操作

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/graph/relations` | 创建关系 |
| POST | `/graph/relations/batch` | 批量创建关系 |
| GET | `/graph/relations` | 获取关系列表 |
| GET | `/graph/relations/{id}` | 获取单个关系 |
| PUT | `/graph/relations/{id}` | 更新关系 |
| DELETE | `/graph/relations/{id}` | 删除关系 |

### NLP 集成

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/graph/store-nlp-results` | 存储 NLP 处理结果 |

### 图查询

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/graph/neighborhood/{entity}` | 获取实体邻域 |
| GET | `/graph/path` | 查找实体间路径 |
| GET | `/graph/data` | 获取图数据（可视化） |
| GET | `/graph/statistics` | 获取统计信息 |

### 管理操作

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/graph/indexes` | 创建索引 |
| GET | `/graph/export` | 导出数据 |
| POST | `/graph/import` | 导入数据 |
| DELETE | `/graph/clear` | 清空数据 |

### API 文档

启动服务后访问：
- Swagger UI: `http://localhost:8000/graph/docs`
- ReDoc: `http://localhost:8000/graph/redoc`

---

## 与 NLP 模块集成

### 方式 1：手动触发存储

```python
from backend.graph_storage.integration import NLPIntegration

# 创建集成服务
integration = NLPIntegration()

# 假设这是 NLP 模块的输出
nlp_response = {
    "status": "success",
    "entities": [
        {"text": "张三", "type": "PERSON", "confidence": 0.95}
    ],
    "relations": [
        {"subject": "张三", "relation": "works_at", "object": "公司A"}
    ]
}

# 处理并存储
result = integration.process_and_store(nlp_response, source_document="doc1.pdf")
```

### 方式 2：自动存储模式

```python
from backend.graph_storage.integration import NLPIntegration

# 启用自动存储
integration = NLPIntegration(auto_store=True)

# 创建钩子函数
store_hook = integration.create_auto_store_hook()

# 在 NLP 处理流程中调用
def process_document(text: str):
    # NLP 处理...
    nlp_result = nlp_service.recognize_entities(text)
    
    # 自动存储到图数据库
    store_hook(nlp_result, source_document="current_doc.pdf")
    
    return nlp_result
```

### 方式 3：通过 API 集成

```bash
# 调用 NLP 实体识别 API
curl -X POST "http://localhost:8000/nlp/entities" \
  -H "Content-Type: application/json" \
  -d '{"text": "张三在阿里巴巴工作"}'

# 将结果存储到图数据库
curl -X POST "http://localhost:8000/graph/store-nlp-results" \
  -H "Content-Type: application/json" \
  -d '{
    "entities": [{"text": "张三", "type": "PERSON"}],
    "relations": [{"subject": "张三", "relation": "works_at", "object": "阿里巴巴"}],
    "source_document": "doc1.pdf"
  }'
```

---

## 数据模型

### 实体 (Entity)

```python
@dataclass
class Entity:
    text: str              # 实体文本
    type: EntityType       # 实体类型
    id: str               # 唯一标识符
    start_pos: int        # 在原文中的起始位置
    end_pos: int          # 结束位置
    confidence: float     # 置信度 (0.0-1.0)
    source_document: str  # 来源文档
    metadata: dict        # 额外元数据
    created_at: datetime  # 创建时间
    updated_at: datetime  # 更新时间
```

**支持的实体类型：**

| 类型 | 说明 | 类型 | 说明 |
|------|------|------|------|
| `PERSON` | 人物 | `ORG` | 组织 |
| `GPE` | 地理政治实体 | `LOC` | 位置 |
| `DATE` | 日期 | `TIME` | 时间 |
| `MONEY` | 货币 | `PERCENT` | 百分比 |
| `FAC` | 设施 | `PRODUCT` | 产品 |
| `EVENT` | 事件 | `WORK_OF_ART` | 艺术作品 |
| `LAW` | 法律 | `LANGUAGE` | 语言 |
| `CARDINAL` | 基数 | `ORDINAL` | 序数 |
| `QUANTITY` | 数量 | `UNKNOWN` | 未知 |

### 关系 (Relation)

```python
@dataclass
class Relation:
    subject: str           # 主体实体文本
    relation: RelationType # 关系类型
    object: str           # 客体实体文本
    id: str               # 唯一标识符
    subject_id: str       # 主体实体 ID
    object_id: str        # 客体实体 ID
    confidence: float     # 置信度
    source_document: str  # 来源文档
    metadata: dict        # 额外元数据
```

**支持的关系类型：**

| 类型 | 说明 | 类型 | 说明 |
|------|------|------|------|
| `works_at` | 工作于 | `lives_in` | 居住于 |
| `born_in` | 出生于 | `studied_at` | 就读于 |
| `married_to` | 配偶 | `parent_of` | 父母 |
| `located_in` | 位于 | `part_of` | 属于 |
| `owns` | 拥有 | `founded_by` | 创立者 |
| `participated_in` | 参与 | `related_to` | 相关 |
| ... | ... | ... | ... |

---

## 部署指南

### Docker Compose 部署

```bash
cd backend
docker-compose up -d
```

这将启动：
- `nlp-service`: NLP 服务 (端口 8000)
- `redis`: 缓存服务
- `neo4j`: 图数据库 (端口 7474, 7687)

### 独立部署 Graph Storage

```bash
# 启动 Neo4j
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password123 \
  neo4j:5-community

# 启动 Graph Storage API
cd backend
python -m graph_storage.main
```

### 生产环境建议

1. **使用强密码**：修改 `NEO4J_AUTH` 和配置文件中的密码
2. **配置持久化**：挂载 Neo4j 数据卷
3. **启用索引**：调用 `/graph/indexes` 创建索引提升查询性能
4. **监控健康**：定期检查 `/graph/health` 端点
5. **备份数据**：使用 `/graph/export` 定期导出数据

---

## 示例代码

### 完整工作流

```python
from backend.graph_storage import (
    connect_neo4j,
    GraphStorage,
    Entity,
    EntityType,
    Relation,
    RelationType
)

# 1. 连接数据库
connector = connect_neo4j(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password123"
)

# 2. 创建存储实例
storage = GraphStorage(connector)

# 3. 创建索引
storage.create_indexes()

# 4. 存储 NLP 结果
result = storage.store_nlp_results(
    entities=[
        {"text": "张三", "type": "PERSON", "confidence": 0.95},
        {"text": "北京大学", "type": "ORG", "confidence": 0.92},
        {"text": "北京", "type": "GPE", "confidence": 0.98}
    ],
    relations=[
        {"subject": "张三", "relation": "studied_at", "object": "北京大学"},
        {"subject": "北京大学", "relation": "located_in", "object": "北京"}
    ],
    source_document="resume.pdf"
)

# 5. 查询实体邻域
neighborhood = storage.get_entity_neighborhood("张三", depth=2)
print(f"节点: {len(neighborhood['nodes'])}, 边: {len(neighborhood['edges'])}")

# 6. 查找路径
paths = storage.find_path("张三", "北京")
print(f"找到 {len(paths)} 条路径")

# 7. 获取统计信息
stats = storage.get_statistics()
print(f"实体总数: {stats['entities']['total']}")
print(f"关系总数: {stats['relations']['total']}")

# 8. 关闭连接
connector.close()
```

---

## 常见问题

### Q: 如何处理连接失败？

```python
from backend.graph_storage import connect_neo4j, Neo4jConnectionError

try:
    connector = connect_neo4j(uri="bolt://localhost:7687", ...)
except Neo4jConnectionError as e:
    print(f"连接失败: {e}")
    # 使用备用方案或重试
```

### Q: 如何批量导入大量数据？

使用批量 API 并分批处理：

```python
# 分批处理，每批 1000 条
batch_size = 1000
for i in range(0, len(entities), batch_size):
    batch = entities[i:i+batch_size]
    storage.entities.create_batch(batch)
```

### Q: 图数据如何可视化？

获取图数据后，可使用前端可视化库：

```python
# 获取图数据
data = storage.get_graph_data(limit=100)

# 返回格式兼容 D3.js / vis.js / Cytoscape.js
# {
#   "nodes": [{"id": "...", "text": "...", "type": "..."}],
#   "edges": [{"source": "...", "target": "...", "type": "..."}]
# }
```

---

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
