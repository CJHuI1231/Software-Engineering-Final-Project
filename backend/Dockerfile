# NLP服务Dockerfile
# 基于Python 3.9 slim镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制requirements文件
COPY requirements.txt .

# 安装系统依赖和Python包
RUN apt-get update && apt-get install -y \
    # 安装Tesseract OCR（如果需要）
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    # 安装其他系统依赖
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p uploads logs

# 暴露端口
EXPOSE 8000

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 运行服务
CMD ["uvicorn", "nlp.main_fastapi:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]




