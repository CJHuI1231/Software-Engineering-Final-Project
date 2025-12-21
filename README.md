# PDF 处理与 NLP 分析系统

这是一个完整的PDF文档处理与自然语言处理系统，整合了PDF解析、文本提取、摘要生成、实体识别和知识图谱可视化功能。

## 功能特点

1. **PDF 处理**
   - 支持直接文本提取和OCR识别
   - 自动判断PDF类型并选择最优解析方式
   - 支持大文件处理（最高100MB）

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

## 安装与设置

### 系统要求

1. Python 3.8+
2. Tesseract OCR
3. Poppler（用于pdf2image）

### 安装步骤

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
   brew install tesseract poppler
   ```

   **Linux (Ubuntu)**:
   ```bash
   sudo apt update
   sudo apt install tesseract-ocr tesseract-ocr-chi-sim poppler-utils
   ```

## 使用方法

### 启动后端服务

```bash
python start_backend.py
```

可选参数：
- `--host`: 服务器主机地址（默认: 0.0.0.0）
- `--port`: 服务器端口（默认: 8000）
- `--reload`: 启用自动重载（开发模式）
- `--workers`: 工作进程数（默认: 4）

### 启动前端服务

```bash
python start_frontend.py
```

可选参数：
- `--port`: 前端服务器端口（默认: 8080）
- `--no-browser`: 不自动打开浏览器

### 使用系统

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
├── requirements.txt            # Python依赖
└── README.md      # 本文档
```

## 进度跟踪

项目整合进度详见 `INTEGRATION_PROGRESS.md`

## 常见问题

1. **Tesseract找不到语言包**
   - 确保已安装中文语言包（chi_sim）
   - 检查TESSDATA_PREFIX环境变量

2. **PDF处理失败**
   - 确保Poppler已正确安装并在PATH中
   - 尝试降低DPI设置

3. **NLP处理速度慢**
   - 尝试使用更小的PDF文件
   - 考虑使用GPU加速（如果可用）

## 贡献

欢迎提交问题报告和功能请求！
