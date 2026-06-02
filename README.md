# PT-ONNX 可视化对比工具 v2.0

目标检测模型的可视化对比工具。支持 PyTorch/ONNX 模型管理、转换、推理可视化和性能对比。

[English](README.md)

## 快速开始

### 开发模式

> 需要：Python 3.8+ 和 Node.js 16+

```bash
# 1. 配置环境（首次）
setup.bat

# 2. 启动前后端
start-dev.bat

# 3. 打开浏览器
http://localhost:5173
```

### 生产模式

> 需要：仅 Python 3.8+（前端打包后）

```bash
# 1. 配置环境（首次）
setup.bat

# 2. 打包前端（首次，需要 Node.js）
build-frontend.bat

# 3. 启动服务
start.bat

# 4. 打开浏览器
http://localhost:8000
```

## 部署到其他电脑

### 方式一：在线部署（目标电脑有网络）

拷贝到目标电脑：
- `backend/`（整个目录）
- `frontend/`（整个目录）
- `setup.bat`
- `start.bat`
- `build-frontend.bat`

在目标电脑上：
```bash
setup.bat           # 安装依赖
build-frontend.bat  # 打包前端
start.bat           # 启动服务
```

### 方式二：离线部署（目标电脑无网络）

在开发电脑上：
```bash
pack-offline.bat    # 下载所有依赖包
build-frontend.bat  # 打包前端
```

拷贝到目标电脑：
- `backend/`
- `frontend/dist/`（打包产物）
- `offline_packages/`
- `setup.bat`
- `start.bat`

在目标电脑上：
```bash
setup.bat   # 从离线包安装
start.bat   # 启动服务
```

## 功能特性

| 功能 | 说明 |
|------|------|
| 模型管理 | 上传 .pt 模型，自动提取元数据，PT→ONNX 转换 |
| 数据集管理 | 导入 YOLO 格式 ZIP 数据集，自动解析类别和统计 |
| 推理可视化 | 支持 PT/ONNX，CPU/GPU，图片/视频，实时检测显示 |
| 性能对比 | PT vs ONNX / PT vs PT / ONNX vs ONNX，速度/内存/FPS 指标 |

## 技术栈

- **后端**：Python 3.8+、FastAPI、SQLAlchemy、SQLite、PyTorch、ONNX Runtime
- **前端**：Vue 3、Element Plus、Pinia、ECharts、Vite

## 项目结构

```
PT-ONNX-benchmark-v2.0/
├── setup.bat               # 环境配置
├── start.bat               # 生产模式启动
├── start-dev.bat           # 开发模式启动
├── build-frontend.bat      # 打包前端
├── pack-offline.bat        # 下载离线包
├── backend/
│   ├── main.py             # 入口文件
│   ├── requirements.txt    # 完整依赖
│   ├── requirements-runtime.txt  # 运行时依赖
│   ├── api/                # API 路由
│   ├── services/           # 业务逻辑
│   ├── engines/            # PT/ONNX 推理引擎
│   ├── db/                 # 数据库
│   ├── schemas/            # Pydantic 模型
│   └── tests/              # 单元测试
├── frontend/
│   ├── package.json
│   ├── src/                # Vue 源码
│   └── dist/               # 打包产物
└── storage/                # 运行时数据（自动创建）
    ├── models/pt/          # PT 模型文件
    ├── models/onnx/        # ONNX 模型文件
    ├── datasets/           # 数据集
    ├── results/            # 推理结果
    └── benchmark.db        # SQLite 数据库
```

## 运行测试

```bash
cd backend
.venv\Scripts\activate
python -m pytest tests/ -v
```

## 常见问题

| 问题 | 解决方案 |
|------|----------|
| "Python not found" | 安装 Python 3.8+，勾选 "Add to PATH" |
| "No module named 'fastapi'" | 运行 `setup.bat` |
| "Frontend not built" | 运行 `build-frontend.bat` |
| "No module named 'ultralytics'" | 可选。运行 `pip install ultralytics` 获取 YOLO 元数据 |
| 端口 8000 被占用 | 修改 `backend/main.py` 中的端口号 |
