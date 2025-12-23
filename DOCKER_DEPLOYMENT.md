# Docker 部署指南

本指南介绍如何使用Docker部署PDF处理与NLP分析系统。

## 前提条件

- 安装 [Docker](https://docs.docker.com/get-docker/)
- 安装 [Docker Compose](https://docs.docker.com/compose/install/)

## 快速开始

1. 克隆或下载项目到本地

2. 在项目根目录运行以下命令：

   ```bash
   docker-compose build backend
   docker-compose up -d
   ```

3. 等待容器启动完成（可能需要几分钟，首次启动需要下载镜像和安装依赖）

4. 在浏览器中访问 http://localhost:8080

## 架构说明

Docker部署包含两个服务：

1. **后端服务**：
   - 基于Python 3.9镜像
   - 包含Tesseract OCR和Poppler
   - 暴露8000端口
   - 提供API服务

2. **前端服务**：
   - 基于Nginx Alpine镜像
   - 暴露8080端口
   - 提供静态文件服务
   - 将API请求代理到后端服务

## 常用命令

### 启动服务
```bash
docker-compose up -d
```

### 查看日志
```bash
# 查看所有服务日志
docker-compose logs

# 查看后端服务日志
docker-compose logs backend

# 查看前端服务日志
docker-compose logs frontend
```

### 停止服务
```bash
docker-compose down
```

### 重新构建镜像
```bash
# 如果修改了代码，需要重新构建
docker-compose build

# 或者强制重新构建（不使用缓存）
docker-compose build --no-cache
```

### 进入后端容器
```bash
docker-compose exec backend bash
```

## 数据持久化

- 代码目录通过volume挂载，修改代码后重启容器即可生效
- 如需持久化数据，可以添加更多volume到docker-compose.yml

## 开发环境

对于开发环境，您可能需要：

1. 修改docker-compose.yml中的volume挂载，确保代码更改能立即生效
2. 使用`docker-compose up`而不是`-d`参数，以便查看实时日志
3. 在Docker容器外安装IDE和开发工具

## 故障排除

### 1. 端口冲突
如果8080或8000端口已被占用，可以修改docker-compose.yml中的端口映射：
```yaml
ports:
  - "8081:8080"  # 将前端服务映射到8081端口
```

### 2. 容器启动失败
查看日志以诊断问题：
```bash
docker-compose logs backend
```

### 3. API请求失败
确保后端服务正常运行：
```bash
curl http://localhost:8000/health
```

### 4. OCR识别效果不佳
Docker镜像已包含中英文OCR语言包，如需其他语言，请修改Dockerfile：
```dockerfile
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-chi-tra \
    tesseract-ocr-jpn  # 添加日语支持
```

## 生产环境部署

对于生产环境，建议：

1. 使用HTTPS：
   - 修改nginx.conf添加SSL配置
   - 更新docker-compose.yml暴露443端口

2. 设置资源限制：
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2.0'
         memory: 4G
   ```

3. 使用外部数据库：
   - 添加数据库服务到docker-compose.yml
   - 修改应用配置连接外部数据库

4. 日志管理：
   - 配置日志轮转
   - 使用集中式日志系统

## 自定义配置

### 1. 修改NLP模型
如需使用不同的NLP模型，可以：
1. 修改backend/nlp/api/中的相关代码
2. 重新构建Docker镜像

### 2. 调整性能参数
可以修改以下文件：
- backend/nlp/main.py - 调整工作进程数
- nginx.conf - 调整Nginx性能参数

### 3. 添加新的API端点
1. 在backend/nlp/api/中创建新的路由文件
2. 在backend/nlp/main.py中注册新路由
3. 重新构建Docker镜像

## 更新部署

当有新版本时：

1. 拉取最新代码：
   ```bash
   git pull
   ```

2. 重新构建并启动：
   ```bash
   docker-compose down
   docker-compose build
   docker-compose up -d
   ```

3. 检查服务状态：
   ```bash
   docker-compose ps
   ```

