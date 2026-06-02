# ============================================
# PT-ONNX Benchmark Tool v2.0
# Docker Image (GPU Support)
# ============================================

# ===== Stage 1: Build Frontend =====
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# 复制前端依赖文件
COPY frontend/package.json frontend/package-lock.json ./

# 安装依赖
RUN npm ci

# 复制前端源码
COPY frontend/ ./

# 构建前端
RUN npm run build

# ===== Stage 2: Production =====
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 创建软链接
RUN ln -sf /usr/bin/python3 /usr/bin/python

WORKDIR /app

# 复制后端依赖文件
COPY backend/requirements-runtime.txt ./requirements.txt

# 安装 Python 依赖
RUN pip install --no-cache-dir \
    torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 && \
    pip install --no-cache-dir onnxruntime-gpu==1.19.0 && \
    pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ ./backend/

# 复制前端构建产物
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# 创建 storage 目录
RUN mkdir -p storage/models/pt \
    storage/models/onnx \
    storage/datasets \
    storage/results

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "backend/main.py"]
