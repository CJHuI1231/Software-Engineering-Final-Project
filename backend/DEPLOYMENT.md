# NLP服务部署指南

## 1. 部署概述

本指南介绍了如何部署NLP处理服务，包括Docker容器化部署、环境配置和运行说明。

## 2. 系统要求

### 2.1 硬件要求
- CPU: 2核心以上
- 内存: 4GB以上
- 存储: 10GB以上可用空间
- 网络: 稳定的网络连接

### 2.2 软件要求
- Docker: 20.10.0+
- Docker Compose: 1.29.0+
- Python: 3.9+
- Redis (可选): 6.0+

## 3. 部署步骤

### 3.1 克隆项目

```bash
git clone <repository-url>
cd backend
```

### 3.2 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt

# 或者使用Docker（推荐）
docker build -t nlp-service .
```

### 3.3 配置环境

#### 3.3.1 环境变量配置

创建`.env`文件：

```bash
cp .env.example .env
```

编辑`.env`文件：

```env
# 应用配置
APP_NAME=NLP Service
APP_VERSION=1.0.0
APP_DESCRIPTION=NLP处理服务

# API配置
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false

# 认证配置
AUTH_ENABLED=false
AUTH_SECRET_KEY=your-secret-key-here
AUTH_ALGORITHM=HS256
AUTH_ACCESS_TOKEN_EXPIRE_MINUTES=30

# 缓存配置
CACHE_ENABLED=true
CACHE_TYPE=redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
CACHE_TTL=3600

# 数据库配置
DATABASE_TYPE=sqlite
DATABASE_PATH=./data/nlp.db

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=./logs/nlp_service.log

# 环境配置
ENVIRONMENT=production
```

#### 3.3.2 配置文件

编辑`deployment_config.yaml`文件，根据需要调整配置。

### 3.4 启动服务

#### 3.4.1 使用Docker Compose

```bash
# 启动所有服务（包括Redis）
docker-compose up -d

# 仅启动NLP服务
docker-compose up -d nlp-service
```

#### 3.4.2 使用Docker直接运行

```bash
# 构建镜像
docker build -t nlp-service .

# 运行容器
docker run -d \
  --name nlp-service \
  -p 8000:8000 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  nlp-service
```

#### 3.4.3 直接运行（开发环境）

```bash
# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate  # Windows

# 运行服务
python nlp/main_fastapi.py
```

## 4. 服务验证

### 4.1 健康检查

```bash
curl http://localhost:8000/health
```

预期响应：

```json
{
  "status": "healthy",
  "timestamp": "2025-12-19T00:00:00Z",
  "services": {
    "entity_recognition": "running",
    "summary": "running"
  }
}
```

### 4.2 API测试

#### 4.2.1 实体识别测试

```bash
curl -X POST http://localhost:8000/api/nlp/entities \
  -H "Content-Type: application/json" \
  -d '{
    "text": "张三在阿里巴巴工作，李四在腾讯上班。"
  }'
```

#### 4.2.2 摘要生成测试

```bash
curl -X POST http://localhost:8000/api/nlp/summary \
  -H "Content-Type: application/json" \
  -d '{
    "text": "这是一个测试文本，用于测试摘要生成功能。文本包含多个句子，每个句子都有不同的内容和结构。我们需要确保摘要能够准确地提取文本的主要信息。",
    "method": "auto"
  }'
```

## 5. 配置管理

### 5.1 环境配置

- 开发环境: `ENVIRONMENT=development`
- 测试环境: `ENVIRONMENT=testing` 
- 生产环境: `ENVIRONMENT=production`

### 5.2 配置文件

主要配置文件：
- `deployment_config.yaml`: 主配置文件
- `.env`: 环境变量配置

### 5.3 配置热更新

某些配置支持热更新，修改后无需重启服务：
- 日志级别
- 缓存配置
- 部分API配置

## 6. 监控和日志

### 6.1 日志查看

```bash
# 查看实时日志
docker-compose logs -f nlp-service

# 查看特定时间范围的日志
docker-compose logs --since="2025-12-19" nlp-service
```

### 6.2 健康监控

访问健康检查端点：`http://localhost:8000/health`

### 6.3 指标收集

访问指标端点：`http://localhost:8000/metrics`

## 7. 维护和更新

### 7.1 服务更新

```bash
# 拉取最新代码
git pull

# 重新构建镜像
docker-compose build

# 重启服务
docker-compose restart nlp-service
```

### 7.2 数据备份

```bash
# 备份SQLite数据库
cp data/nlp.db backups/nlp_$(date +%Y%m%d).db

# 备份日志
cp logs/nlp_service.log backups/nlp_$(date +%Y%m%d).log
```

### 7.3 清理资源

```bash
# 停止并删除容器
docker-compose down

# 清理未使用的镜像和卷
docker system prune -f
```

## 8. 故障排除

### 8.1 常见问题

#### 8.1.1 服务无法启动
- 检查端口是否被占用：`netstat -tuln | grep 8000`
- 检查Docker服务状态：`docker ps -a`
- 查看详细错误日志：`docker-compose logs nlp-service`

#### 8.1.2 API调用失败
- 检查网络连接
- 验证API密钥（如果启用）
- 检查请求格式和参数

#### 8.1.3 内存不足
- 增加容器内存限制
- 优化模型加载和推理
- 启用缓存机制

### 8.2 联系支持

如果遇到无法解决的问题，请联系：
- 邮箱: support@example.com
- 问题跟踪: https://github.com/your-org/nlp-service/issues

## 9. 安全注意事项

### 9.1 认证和授权
- 生产环境建议启用API密钥认证
- 定期更新密钥
- 限制API访问权限

### 9.2 数据安全
- 敏感数据加密存储
- 定期备份重要数据
- 监控异常访问

### 9.3 系统安全
- 定期更新Docker和依赖
- 限制容器权限
- 启用防火墙规则

## 10. 性能优化

### 10.1 缓存优化
- 启用Redis缓存
- 合理设置缓存TTL
- 监控缓存命中率

### 10.2 并行处理
- 调整工作线程数
- 优化批处理大小
- 监控CPU和内存使用

### 10.3 模型优化
- 使用量化模型
- 启用模型缓存
- 监控模型加载时间

## 11. 扩展部署

### 11.1 Kubernetes部署
```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nlp-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nlp-service
  template:
    metadata:
      labels:
        app: nlp-service
    spec:
      containers:
      - name: nlp-service
        image: your-registry/nlp-service:1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: production
```

### 11.2 负载均衡
```yaml
# k8s-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: nlp-service
spec:
  selector:
    app: nlp-service
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

## 12. 版本管理

### 12.1 版本标签
- 使用语义化版本：MAJOR.MINOR.PATCH
- 版本发布流程：
  1. 开发阶段
  2. 测试阶段  
  3. 预发布阶段
  4. 生产发布

### 12.2 回滚策略
- 保留最近3个版本的镜像
- 快速回滚机制
- 数据迁移计划

---

*文档版本：1.0*
*最后更新：2025年12月19日*



