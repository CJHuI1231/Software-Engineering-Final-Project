# Docker 部署故障排除指南

## 常见问题与解决方案

### 1. Docker 连接错误

**错误信息**: `unable to get image 'redis:6.2-alpine': error during connect`

**可能原因**:
- Docker Desktop 未启动
- Docker 守护进程连接问题
- 网络配置问题

**解决方案**:

#### Windows 用户

1. **检查 Docker Desktop**:
   - 确保Docker Desktop已启动
   - 尝试重启Docker Desktop
   - 检查Docker Desktop是否设置为"使用WSL 2"

2. **检查 Docker 服务**:
   ```powershell
   # 以管理员身份运行PowerShell
   Get-Service docker
   Start-Service docker
   ```

3. **重置 Docker**:
   ```powershell
   # 重置Docker网络
   docker network prune
   
   # 重置Docker系统
   docker system prune -a
   ```

4. **使用WSL2后端**:
   - 在Docker Desktop设置中，确保"使用WSL 2引擎"已启用
   - 重启Docker Desktop

5. **使用本地镜像**:
   - 如果问题持续，可以尝试使用已存在的镜像：
   ```bash
   docker images
   # 查看是否有可用的redis镜像
   ```

#### Linux/Mac 用户

1. **检查 Docker 服务**:
   ```bash
   sudo systemctl status docker
   sudo systemctl start docker
   ```

2. **检查 Docker 用户权限**:
   ```bash
   sudo usermod -aG docker $USER
   # 重新登录或重启
   ```

### 2. Docker Compose 版本警告

**错误信息**: `attribute 'version' is obsolete, it will be ignored`

**原因**: 新版本的Docker Compose不再需要version字段

**解决方案**:
- 从docker-compose.yml中删除version行
- 这只是一个警告，不会影响功能

### 3. 端口冲突

**错误信息**: `Port is already allocated`

**解决方案**:
1. 修改docker-compose.yml中的端口映射:
   ```yaml
   ports:
     - "8081:8080"  # 前端使用8081
     - "8001:8000"  # 后端使用8001
   ```

2. 或者停止占用端口的服务:
   ```bash
   # 查找占用端口的进程
   netstat -tulpn | grep :8080
   
   # 停止服务（Linux）
   sudo kill -9 <PID>
   ```

### 4. 容器启动失败

**错误信息**: 各种容器启动错误

**解决方案**:
1. 查看详细日志:
   ```bash
   docker-compose logs -f [服务名]
   ```

2. 重新构建镜像:
   ```bash
   docker-compose build --no-cache [服务名]
   ```

3. 检查磁盘空间:
   ```bash
   df -h
   ```

4. 检查Docker资源限制:
   - 在Docker Desktop中调整资源分配

### 5. Windows 特定问题

#### 文件路径问题

**问题**: Windows路径与Docker容器路径映射不正确

**解决方案**:
1. 使用正斜杠:
   ```yaml
   volumes:
     - D:/Software-Engineering-Final-Project/backend:/app/backend
   ```

2. 或使用相对路径:
   ```yaml
   volumes:
     - ./backend:/app/backend
   ```

3. 确保路径没有特殊字符

#### 权限问题

**问题**: Docker没有足够权限访问文件

**解决方案**:
1. 确保Docker Desktop有足够权限
2. 使用管理员身份运行PowerShell
3. 检查文件夹权限设置

### 6. 替代部署方案

如果Docker问题持续存在，可以考虑以下替代方案:

#### 1. 仅使用Docker运行后端

```bash
# 构建后端镜像
docker build -t pdf-nlp-backend .

# 运行后端容器
docker run -d -p 8000:8000 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/logs:/app/logs \
  pdf-nlp-backend

# 本地运行前端
python start_frontend.py
```

#### 2. 仅使用Docker运行数据库

```yaml
# docker-compose-db.yml
version: '3.8'

services:
  redis:
    image: "redis:6.2-alpine"
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  neo4j:
    image: neo4j:5-community
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/password123
    volumes:
      - neo4j_data:/data

volumes:
  redis_data:
  neo4j_data:
```

```bash
# 启动数据库服务
docker-compose -f docker-compose-db.yml up -d

# 本地运行应用
python start_backend.py
python start_frontend.py
```

#### 3. 完全本地部署

参考README.md中的本地部署说明。

### 7. 性能优化

1. **分配更多资源**:
   - 在Docker Desktop中增加内存和CPU限制

2. **使用SSD存储**:
   - 确保Docker使用SSD存储

3. **优化镜像大小**:
   - 使用多阶段构建
   - 清理不必要的包

### 8. 日志收集

**收集完整的错误信息**:
```bash
# 创建日志目录
mkdir -p docker-logs

# 导出所有服务的日志
docker-compose logs --no-color > docker-logs/all.log
docker-compose logs backend > docker-logs/backend.log
docker-compose logs frontend > docker-logs/frontend.log
docker-compose logs redis > docker-logs/redis.log
docker-compose logs neo4j > docker-logs/neo4j.log

# 导出容器信息
docker inspect $(docker-compose ps -q) > docker-logs/containers.json
```

### 9. 社区资源

如果问题仍然存在，可以寻求帮助:
- [Docker Desktop 官方文档](https://docs.docker.com/desktop/)
- [Docker Compose 官方文档](https://docs.docker.com/compose/)
- [GitHub Issues](https://github.com/docker/compose/issues)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/docker)

---

## 快速检查清单

- [ ] Docker Desktop已启动
- [ ] 没有其他应用占用8080和8000端口
- [ ] 有足够的磁盘空间
- [ ] 网络连接正常
- [ ] 文件路径没有特殊字符
- [ ] 防火墙没有阻止Docker

