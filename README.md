# PDF 处理与 NLP 分析系统

这是一个完整的PDF文档处理与自然语言处理系统，整合了PDF解析、文本提取、摘要生成、实体识别和知识图谱可视化功能。

## 功能特点

1. **PDF 处理**
   - 支持直接文本提取和OCR识别
   - 自动判断PDF类型并选择最优解析方式
   - 支持大文件处理（最高100MB）
   - 图像预处理提高OCR准确率

2. **摘要生成**
   - 支持多种摘要方法（BART、TextRank、自动选择）
   - 提供摘要质量评估指标

3. **实体识别**
   - 识别文本中的人物、组织、日期、地点等实体
   - 支持实体关系提取

4. **知识图谱**
   - 可视化实体关系
   - 交互式图谱展示

## 系统架构

- **后端**: FastAPI + NLP服务
- **前端**: HTML/CSS/JavaScript + PDF.js
- **PDF处理**: pdf2image + pytesseract + pdfplumber
- **NLP处理**: transformers + spacy + NLTK
- **数据库**: Neo4j (图数据库) + Redis (缓存)

## 部署方式

本项目支持两种部署方式：Docker部署（推荐）和本地部署。

### 方式一：Docker部署（推荐）

#### 前提条件
- 安装 [Docker](https://docs.docker.com/get-docker/)
- 安装 [Docker Compose](https://docs.docker.com/compose/install/)

#### 部署步骤

1. 克隆或下载项目到本地

2. 在项目根目录运行以下命令：

   ```bash
   docker-compose up -d --build backend
   docker-compose up -d frontend
   ```

3. 等待容器启动完成（可能需要几分钟，首次启动需要下载镜像和安装依赖）

4. 在浏览器中访问 http://localhost:8080

#### Docker架构

Docker部署包含四个服务：

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

3. **Redis缓存服务**：
   - 用于缓存NLP处理结果

4. **Neo4j图数据库服务**：
   - 存储知识图谱数据
   - 提供图查询和可视化功能

#### 常用Docker命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重新构建镜像
docker-compose build

# 进入后端容器
docker-compose exec backend bash
```

### 方式二：本地部署

#### 系统要求

1. Python 3.8+
2. Tesseract OCR
3. Poppler（用于pdf2image）
4. Redis（可选，用于缓存）
5. Neo4j（可选，用于知识图谱存储）

#### 安装步骤

1. 克隆或下载项目
2. 安装Python依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 安装系统依赖：

   **Windows**:
   - 安装 Tesseract OCR：从 [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) 下载并安装
   - 安装 Poppler：从 [poppler-windows](https://github.com/oschwartz10612/poppler-windows) 下载并解压，将bin目录添加到PATH

   **macOS**:
   ```bash
   brew install tesseract poppler redis neo4j
   ```

   **Linux (Ubuntu)**:
   ```bash
   sudo apt update
   sudo apt install tesseract-ocr tesseract-ocr-chi-sim poppler-utils redis-server neo4j
   ```

#### 本地启动

1. 启动Redis（如果使用）：
   ```bash
   redis-server
   ```

2. 启动Neo4j（如果使用）：
   ```bash
   neo4j start
   ```

3. 启动后端服务：
   ```bash
   python start_backend.py
   ```

4. 启动前端服务：
   ```bash
   python start_frontend.py
   ```

5. 在浏览器中访问 `http://localhost:8080`

## 使用系统

1. 在浏览器中访问 `http://localhost:8080`
2. 点击"上传文件"按钮，选择PDF文件
3. 等待PDF处理完成
4. 点击"生成摘要"按钮获取文档摘要
5. 切换到"知识图谱"选项卡，点击"生成知识图谱"按钮可视化实体关系

## API文档

后端API文档可在 `http://localhost:8000/docs` 查看

主要API端点：
- `POST /api/pdf/upload` - 上传PDF文件
- `POST /api/pdf/summary` - 生成摘要
- `POST /api/pdf/entities` - 提取实体
- `POST /api/pdf/knowledge_graph` - 生成知识图谱

## 项目结构

```
Software-Engineering-Final-Project/
├── backend/                     # 后端代码
│   ├── nlp/                    # NLP服务
│   │   ├── api/                # API路由
│   │   │   ├── pdf_api.py      # PDF处理API
│   │   │   ├── summary_api.py  # 摘要生成API
│   │   │   └── entity_api.py   # 实体识别API
│   │   ├── entity_recognition/   # 实体识别模块
│   │   ├── summary/            # 摘要生成模块
│   │   └── utils/              # 工具模块
│   └── OCR/                   # PDF OCR模块
│       └── PDF_OCR.py          # PDF解析器
├── web_fronted/                # 前端代码
│   ├── index.html              # 主页面
│   ├── main.js                 # JavaScript逻辑
│   └── styles.css              # 样式表
├── start_backend.py            # 后端启动脚本
├── start_frontend.py           # 前端启动脚本
├── Dockerfile                 # Docker镜像构建文件
├── docker-compose.yml         # Docker Compose配置
├── nginx.conf                # Nginx配置文件
├── requirements.txt           # Python依赖
├── README.md                # 本文档
├── README_INTEGRATION.md     # 整合说明文档
├── DOCKER_DEPLOYMENT.md     # Docker部署详细说明
└── INTEGRATION_PROGRESS.md   # 整合进度跟踪
```

## 进度跟踪

项目整合进度详见 `INTEGRATION_PROGRESS.md`

## 常见问题

### Docker部署

1. **端口冲突**
   如果8080或8000端口已被占用，可以修改docker-compose.yml中的端口映射

2. **容器启动失败**
   查看日志以诊断问题：
   ```bash
   docker-compose logs backend
   ```

3. **API请求失败**
   确保后端服务正常运行：
   ```bash
   curl http://localhost:8000/health
   ```

### 本地部署

1. **Tesseract找不到语言包**
   - 确保已安装中文语言包（chi_sim）
   - 检查TESSDATA_PREFIX环境变量

2. **PDF处理失败**
   - 确保Poppler已正确安装并在PATH中
   - 尝试降低DPI设置

3. **NLP处理速度慢**
   - 尝试使用更小的PDF文件
   - 考虑使用GPU加速（如果可用）

## 性能优化

1. **大文件处理**
   - 系统自动对大文件（>10MB）进行优化处理
   - 对文本进行截取以避免处理超时

2. **缓存机制**
   - Redis缓存NLP处理结果
   - 前端缓存静态资源

3. **并发处理**
   - FastAPI支持多进程工作
   - 可通过`--workers`参数调整

## 贡献

欢迎提交问题报告和功能请求！

## 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。