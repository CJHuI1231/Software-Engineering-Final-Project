# 1. 使用你指定的本地/自定义镜像
FROM lindozy/python3.11

# 2. 设置工作目录
WORKDIR /app

# 3. 设置环境变量
# PYTHONDONTWRITEBYTECODE: 防止Python生成.pyc文件
# PYTHONUNBUFFERED: 确保日志即时输出
# DEBIAN_FRONTEND: 避免apt安装时出现交互式提示
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# 4. 配置 APT 使用国内镜像源 (强烈建议保留，否则安装 OCR 会很慢)
# 注意：这里假设基础镜像是基于 Debian Bookworm (Python 3.11 默认)
# 如果构建报错找不到文件，可以尝试注释掉这两行 sed 命令
#RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
 #   sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# 5. 安装系统依赖 (合并命令以减少镜像层数)
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Tesseract OCR 核心及中文语言包
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-chi-tra \
    # PDF处理工具
    poppler-utils \
    # 常用工具
    curl \
    wget \
    git \
    # 清理缓存以减小镜像大小
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 6. 配置 pip 镜像源 (阿里源)
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set install.trusted-host mirrors.aliyun.com

# 7. 复制依赖文件 (利用Docker缓存层，仅当requirements变化时才重新安装)
COPY requirements.txt .

# 8. 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 9. 复制剩余的应用代码
COPY . .

# 10. 创建必要的运行时目录
RUN mkdir -p uploads logs cache

# 11. 安全性：创建非root用户并切换
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

# 切换到非root用户
USER app

# 12. 暴露端口
EXPOSE 8000

# 13. 启动命令
CMD ["python", "start_backend.py", "--host", "0.0.0.0", "--port", "8000"]