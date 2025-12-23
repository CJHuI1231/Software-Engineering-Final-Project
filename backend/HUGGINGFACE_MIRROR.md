# Hugging Face 镜像配置说明

## 问题描述

在中国大陆地区，直接访问 Hugging Face (https://huggingface.co) 可能会遇到网络连接问题，导致无法下载预训练模型。

## 解决方案

### 方案 1：使用镜像（推荐，已配置）

本项目已配置使用 Hugging Face 镜像站点 `https://hf-mirror.com`，该镜像站点由国内志愿者维护，可以正常访问。

#### 已完成的配置

1. **代码层面配置**
   - `backend/nlp/entity_recognition/entity_recognition.py` - 添加了 HF_ENDPOINT 环境变量
   - `backend/nlp/summary/summary_model.py` - 添加了 HF_ENDPOINT 环境变量

2. **Docker Compose 配置**
   - `docker-compose.yml` - 添加了 HF_ENDPOINT 环境变量

#### 使用方法

在 `.env` 文件中添加（可选，默认已设置为 https://hf-mirror.com）：
```bash
HF_ENDPOINT=https://hf-mirror.com
```

### 方案 2：使用本地缓存模型

如果镜像站点仍然无法访问，可以手动下载模型并缓存到本地。

#### 步骤 1：手动下载模型

```bash
# 进入容器
docker exec -it pdf_nlp_backend bash

# 设置 Hugging Face 镜像
export HF_ENDPOINT=https://hf-mirror.com

# 下载实体识别模型
python3 -c "from transformers import pipeline; pipeline('ner', model='ckiplab/bert-base-chinese-ner')"

# 下载摘要模型
python3 -c "from transformers import pipeline; pipeline('summarization', model='OpenMOSS-Team/bart-base-chinese')"

# 退出容器
exit
```

#### 步骤 2：重启容器

```bash
docker restart pdf_nlp_backend
```

### 方案 3：离线安装模型

如果完全无法访问 Hugging Face，可以提前下载模型文件，然后挂载到容器中。

#### 步骤 1：在有网络的机器上下载模型

```bash
# 安装 huggingface-cli
pip install -U huggingface_hub

# 下载模型到本地
huggingface-cli download ckiplab/bert-base-chinese-ner --local-dir ./models/ckiplab-bert-base-chinese-ner
huggingface-cli download OpenMOSS-Team/bart-base-chinese --local-dir ./models/OpenMOSS-bart-base-chinese
```

#### 步骤 2：将模型文件复制到服务器

将 `./models` 目录上传到服务器，并挂载到容器中。

#### 步骤 3：修改 docker-compose.yml

```yaml
volumes:
  # 添加模型目录挂载
  - ./models:/app/models
```

#### 步骤 4：修改代码使用本地模型

在 `backend/nlp/entity_recognition/entity_recognition.py` 中：

```python
self.transformer_pipeline = pipeline(
    "ner",
    model="/app/models/ckiplab-bert-base-chinese-ner",
    aggregation_strategy="simple"
)
```

在 `backend/nlp/summary/summary_model.py` 中：

```python
self.transformer_pipeline = pipeline(
    "summarization",
    model="/app/models/OpenMOSS-bart-base-chinese",
    tokenizer="/app/models/OpenMOSS-bart-base-chinese"
)
```

### 方案 4：使用代理（不推荐）

如果公司或学校有代理服务器，可以配置 Hugging Face 使用代理。

```bash
# 在 docker-compose.yml 中添加
environment:
  - HTTP_PROXY=http://your-proxy:port
  - HTTPS_PROXY=http://your-proxy:port
  - NO_PROXY=localhost,127.0.0.1
```

## 验证配置

### 检查镜像是否生效

```bash
# 进入容器
docker exec -it pdf_nlp_backend bash

# 检查环境变量
echo $HF_ENDPOINT

# 测试模型加载
python3 << EOF
import os
print(f"HF_ENDPOINT: {os.environ.get('HF_ENDPOINT', 'Not set')}")
from transformers import pipeline
print("正在加载模型...")
try:
    pipe = pipeline('ner', model='ckiplab/bert-base-chinese-ner')
    print("模型加载成功！")
except Exception as e:
    print(f"模型加载失败: {e}")
EOF
```

## 常见问题

### Q1: 即使设置了镜像，仍然无法下载模型？

**A:** 可能原因：
1. 镜像站点临时不可用，可以尝试其他镜像：
   - `https://hf-mirror.com` (推荐)
   - `https://hf.ainemo.cn`
   - `https://hf.guyue.moe`

2. 模型名称在镜像上不存在，需要检查对应的镜像站是否同步了该模型。

### Q2: 如何查看已下载的模型？

**A:**
```bash
# 进入容器
docker exec -it pdf_nlp_backend bash

# 查看缓存目录
ls -la ~/.cache/huggingface/hub/
```

### Q3: 如何清理模型缓存？

**A:**
```bash
# 进入容器
docker exec -it pdf_nlp_backend bash

# 清理缓存
rm -rf ~/.cache/huggingface/hub/*
```

### Q4: 模型下载失败后，如何重试？

**A:**
```bash
# 重启容器
docker restart pdf_nlp_backend

# 或删除缓存后重试
docker exec -it pdf_nlp_backend bash
rm -rf ~/.cache/huggingface/hub/*
exit
docker restart pdf_nlp_backend
```

## 当前项目使用的模型

1. **实体识别模型**: `ckiplab/bert-base-chinese-ner`
2. **摘要模型**: `OpenMOSS-Team/bart-base-chinese`

## 推荐做法

对于生产环境，建议：
1. 使用镜像站点进行首次下载
2. 将下载的模型打包保存
3. 在部署时直接使用本地模型，避免每次都下载

这样可以：
- 提高部署速度
- 减少对外部依赖
- 确保模型版本一致

