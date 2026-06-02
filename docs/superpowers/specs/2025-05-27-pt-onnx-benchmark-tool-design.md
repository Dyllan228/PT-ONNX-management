# PT-ONNX 可视化对比工具设计文档

## 1. 项目概述

构建一个基于 Web 的 PyTorch 与 ONNX 模型可视化对比工具，支持模型管理、自动转换、推理可视化和多维度性能对比。采用多标签页 SPA 架构，单机本地部署。

### 核心目标

- 自动将 PT 模型转换为 ONNX 模型
- 在同一数据源上分别用 PT 和 ONNX 推理，可视化检测结果
- 对比推理速度、检测精度、算力需求、资源占用等指标
- 支持 PT↔ONNX 纵向对比和不同版本 PT 间横向对比
- 启动时自动扫描本地文件作为默认数据，降低使用门槛

## 2. 技术选型

| 层级 | 技术 | 理由 |
|------|------|------|
| 前端框架 | Vue 3 + Composition API | 国内主流，生态成熟 |
| UI 组件库 | Element Plus | 多标签页、表格、表单、上传等开箱即用 |
| 前端路由 | Vue Router | 标签页路由管理 |
| 状态管理 | Pinia | 轻量，Vue 3 官方推荐 |
| 图表库 | ECharts | 柱状图、折线图、雷达图，国产首选 |
| HTTP 客户端 | Axios | 请求 + 轮询封装 |
| 后端框架 | FastAPI | 异步支持，自动 API 文档，Python 生态无缝集成 |
| 数据库 | SQLite | 单机部署，零配置 |
| ORM | SQLAlchemy | FastAPI 生态标准搭配 |
| PT 推理 | PyTorch | 模型加载和推理 |
| ONNX 推理 | ONNX Runtime | ONNX 模型推理，支持 CPU/CUDA |
| ASGI 服务器 | Uvicorn | FastAPI 标准运行时 |

## 3. 整体架构

```
┌─────────────────────────────────────────────────────┐
│                    Vue 3 SPA 前端                     │
│  ┌──────────┬──────────┬──────────┬──────────┬─────┐ │
│  │ 模型管理  │ 模型转换  │ 推理可视化│ 性能对比 │版本管理│ │
│  └──────────┴──────────┴──────────┴──────────┴─────┘ │
│          Vue Router + Pinia + ECharts + Axios        │
└──────────────────────┬──────────────────────────────┘
                       │ REST API + 轮询
┌──────────────────────┴──────────────────────────────┐
│                   FastAPI 后端                        │
│                                                      │
│  ┌───────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ API 路由层 │  │ 业务服务层    │  │  任务管理器   │  │
│  └───────────┘  └──────────────┘  └──────────────┘  │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐                 │
│  │ PyTorch 引擎  │  │ ONNX 引擎    │                 │
│  │ (CPU / CUDA)  │  │ (CPU / CUDA) │                 │
│  └──────────────┘  └──────────────┘                 │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐                 │
│  │  SQLite 存储  │  │ 文件系统存储  │                 │
│  └──────────────┘  └──────────────┘                 │
└──────────────────────────────────────────────────────┘
```

### 前后端通信方式

采用 REST API + 轮询（方案 A）：
- 常规操作（CRUD）直接通过 REST API 同步返回
- 耗时操作（转换、推理、对比）提交后返回 `task_id`，前端每 1-2 秒轮询任务状态
- 单机部署网络延迟为零，轮询完全够用

## 4. 前端设计

### 4.1 标签页布局

使用 Element Plus `el-tabs` 实现顶部标签页，每个标签页对应独立路由和组件页面：

| 标签页 | 路由 | 核心功能 |
|--------|------|----------|
| 模型管理 | `/models` | 上传 PT 模型，自动扫描注册，元数据展示，手动编辑信息 |
| 模型转换 | `/convert` | 选择 PT 模型，配置导出参数，执行转换，查看进度和日志 |
| 推理可视化 | `/inference` | 选择模型+数据源+硬件，运行推理，展示标注后的检测结果 |
| 性能对比 | `/benchmark` | 选择对比模式和模型，执行批量对比，图表化展示结果 |
| 版本管理 | `/versions` | 模型版本列表，历史记录，指标快照，版本回溯和删除 |

### 4.2 前端目录结构

```
frontend/
├── public/
├── src/
│   ├── api/                    # API 请求封装
│   │   ├── models.js
│   │   ├── convert.js
│   │   ├── inference.js
│   │   ├── benchmark.js
│   │   ├── datasets.js
│   │   └── tasks.js
│   ├── components/             # 公共组件
│   │   ├── TaskProgress.vue    # 任务进度条（复用）
│   │   ├── ResultImage.vue     # 标注结果图展示
│   │   ├── MetricsChart.vue    # 性能指标图表
│   │   └── FileUploader.vue    # 文件上传组件
│   ├── views/                  # 标签页页面
│   │   ├── ModelManager.vue    # 模型管理
│   │   ├── ModelConvert.vue    # 模型转换
│   │   ├── InferenceVisual.vue # 推理可视化
│   │   ├── PerformanceCompare.vue # 性能对比
│   │   └── VersionManage.vue   # 版本管理
│   ├── stores/                 # Pinia 状态
│   │   ├── models.js           # 模型列表状态
│   │   └── tasks.js            # 任务状态
│   ├── router/
│   │   └── index.js            # 路由配置
│   ├── utils/
│   │   └── polling.js          # 轮询封装
│   ├── App.vue
│   └── main.js
├── package.json
└── vite.config.js
```

### 4.3 默认值与自动扫描

页面加载时自动获取已有数据，填充默认选项：

| 页面 | 组件 | 默认值逻辑 |
|------|------|-----------|
| 模型管理 | 模型列表 | 启动即展示已扫描到的模型，无需手动上传 |
| 模型转换 | 模型下拉框 | 默认选中目录中第一个 PT 模型 |
| 推理可视化 | 模型选择 | 默认选中第一个模型 |
| 推理可视化 | 数据源选择 | 默认选中目录中的测试视频，同时提供"上传新文件"选项 |
| 性能对比 | 对比模式 | 默认选中 PT vs ONNX |
| 性能对比 | 模型勾选 | 同名多版本默认全勾选 |
| 性能对比 | 硬件选择 | 默认勾选 CPU（GPU 可能不可用） |

### 4.4 推理可视化展示方案

**图片结果：**
- 后端返回标注后的图片（检测框 + 类别 + 置信度）
- 前端用 `<el-image>` 展示，支持缩放
- PT vs ONNX 模式下左右并排展示

**视频结果：**
- 后端逐帧处理，保存标注帧图到 `results/{task_id}/frames/`
- 前端提供帧浏览控件（滑动条 + 上一帧/下一帧按钮）
- 同时展示每帧检测统计信息

**检测信息表格：**

每帧/每图下方附带表格，列出所有检测目标的类别、置信度、边界框坐标。

## 5. 后端设计

### 5.1 目录结构

```
backend/
├── main.py                     # FastAPI 入口，启动时扫描
├── api/                        # API 路由层
│   ├── models.py               # 模型 CRUD + 上传
│   ├── convert.py              # 转换任务
│   ├── inference.py            # 推理任务
│   ├── benchmark.py            # 性能对比任务
│   ├── datasets.py             # 数据源管理
│   └── tasks.py                # 通用任务查询
├── services/                   # 业务服务层
│   ├── model_service.py        # 模型元数据提取、自动描述
│   ├── convert_service.py      # PT → ONNX 转换
│   ├── inference_service.py    # 推理引擎调度
│   ├── benchmark_service.py    # 多硬件性能测试
│   └── scan_service.py         # 目录扫描服务
├── engines/                    # 推理引擎
│   ├── pt_engine.py            # PyTorch 推理封装
│   └── onnx_engine.py          # ONNX Runtime 推理封装
├── db/
│   ├── database.py             # SQLAlchemy 引擎
│   └── models.py               # 数据库表模型
├── storage/                    # 文件存储
│   └── file_manager.py         # 文件路径管理
└── schemas/                    # Pydantic 请求/响应模型
    ├── model_schema.py
    ├── convert_schema.py
    ├── inference_schema.py
    └── benchmark_schema.py
```

### 5.2 启动时自动扫描

FastAPI 启动时执行 `startup_event`：

1. 初始化 SQLite 数据库
2. 扫描项目根目录和 `storage/models/pt/` 中的 `.pt` 文件
3. 对每个 PT 文件：提取元数据（模型结构、参数量、类别数等），自动注册到 `models` 表
4. 检查是否存在对应 `.onnx` 文件，标记转换状态
5. 扫描项目根目录和 `storage/uploads/` 中的图片/视频文件，注册为数据源
6. 启动 API 服务

### 5.3 异步任务机制

采用 `concurrent.futures.ThreadPoolExecutor` + 数据库状态跟踪：

1. 前端 POST 请求创建任务 → 后端返回 `task_id`，立即响应
2. 后端将任务提交到线程池
3. 线程执行过程中更新 `tasks` 表的 `progress`、`status`
4. 前端每 1-2 秒轮询 `GET /api/tasks/{task_id}` 获取进度
5. 任务完成，`status` 变为 `completed`，前端获取结果

## 6. 数据模型

### 6.1 数据库设计（SQLite）

**models 表 — 模型管理表（以 PT 为核心）**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| name | VARCHAR | 模型名称（如 "helmet-vest"，同源模型多版本共享） |
| version | VARCHAR | 版本标识（如 "v1-50epoch", "v2-100epoch"） |
| pt_file_path | VARCHAR | PT 文件路径 |
| onnx_file_path | VARCHAR | ONNX 文件路径（转换后填入） |
| onnx_converted | BOOLEAN | 是否已转换为 ONNX |
| description | TEXT | 自动生成的描述 |
| class_names | JSON | 检测类别列表 |
| input_size | JSON | 输入尺寸 [H, W] |
| param_count | BIGINT | 参数量 |
| pt_file_size | BIGINT | PT 文件大小 (bytes) |
| onnx_file_size | BIGINT | ONNX 文件大小 (bytes) |
| training_epochs | INTEGER | 训练轮数 |
| training_samples | INTEGER | 训练数据量 |
| created_at | DATETIME | 创建时间 |

设计要点：一条记录 = 一个 PT 模型 +（可选的）一个对应 ONNX 模型，天然保证一对一关系。

**tasks 表 — 异步任务表**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR PK | UUID |
| type | VARCHAR | `convert` / `inference` / `benchmark` |
| status | VARCHAR | `pending` / `running` / `completed` / `failed` |
| progress | INTEGER | 0-100 |
| params | JSON | 任务参数 |
| result | JSON | 结果数据（指标、输出路径等） |
| error_msg | TEXT | 错误信息 |
| created_at | DATETIME | 创建时间 |
| finished_at | DATETIME | 结束时间 |

**benchmark_records 表 — 性能记录表**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| task_id | VARCHAR FK | 关联任务 |
| model_id | INTEGER FK | 关联模型 |
| model_type | VARCHAR | `pt` 或 `onnx` |
| device | VARCHAR | `cpu` / `cuda` |
| avg_inference_ms | FLOAT | 平均推理耗时 |
| avg_preprocess_ms | FLOAT | 平均预处理耗时 |
| avg_postprocess_ms | FLOAT | 平均后处理耗时 |
| peak_memory_mb | FLOAT | 峰值内存 (MB) |
| model_size_mb | FLOAT | 模型文件大小 (MB) |
| fps | FLOAT | 每秒帧数 |
| precision_metrics | JSON | 精度指标（mAP、IoU 等） |
| created_at | DATETIME | 创建时间 |

### 6.2 文件存储结构

```
PT-ONNX-benchmark-v2.0/
├── helmet-vest-v1.pt          # 预置默认模型（启动自动识别）
├── 反光衣测试.mp4              # 预置默认数据源（启动自动识别）
├── backend/
├── frontend/
└── storage/
    ├── models/
    │   ├── pt/                # 新上传的 PT 模型
    │   └── onnx/              # 转换后的 ONNX 模型
    ├── uploads/
    │   ├── images/            # 上传的检测图片
    │   └── videos/            # 上传的检测视频
    └── results/
        └── {task_id}/         # 推理/对比结果
            ├── annotated/     # 标注后的图片/帧
            └── logs/          # 详细日志
```

## 7. API 设计

### 7.1 模型管理 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/models` | 获取所有模型列表 |
| GET | `/api/models/{id}` | 获取单个模型详情 |
| POST | `/api/models/upload` | 上传 PT 模型文件 |
| PUT | `/api/models/{id}` | 更新模型信息 |
| DELETE | `/api/models/{id}` | 删除模型及其 ONNX |
| POST | `/api/models/scan` | 手动触发重新扫描目录 |

### 7.2 数据源 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/datasets` | 获取已有数据源列表 |
| POST | `/api/datasets/upload` | 上传新的检测数据 |

### 7.3 模型转换 API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/convert` | 创建转换任务，返回 task_id |
| GET | `/api/convert/{task_id}` | 查询转换进度和日志 |

### 7.4 推理 API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/inference` | 创建推理任务 |
| GET | `/api/inference/{task_id}` | 查询推理进度和结果 |
| GET | `/api/inference/{task_id}/image/{frame}` | 获取标注后的结果图 |

### 7.5 性能对比 API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/benchmark` | 创建对比任务 |
| GET | `/api/benchmark/{task_id}` | 查询对比进度和结果 |

### 7.6 任务通用 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/tasks/{task_id}` | 查询任意任务状态 |
| DELETE | `/api/tasks/{task_id}` | 取消/删除任务 |

## 8. 性能对比设计

### 8.1 三种对比模式

| 对比模式 | 说明 | 示例 |
|---------|------|------|
| PT ↔ ONNX 纵向 | 同一模型 PT 与 ONNX 的性能差异 | helmet-vest-v1.pt vs helmet-vest-v1.onnx |
| PT ↔ PT 横向 | 同名模型不同训练版本的差异 | v1-50epoch vs v2-100epoch vs v3-200epoch |
| ONNX ↔ ONNX 横向 | 不同版本转换出的 ONNX 之间的差异 | v1.onnx vs v2.onnx vs v3.onnx |

### 8.2 对比指标

**推理速度：**
- 平均推理耗时（ms）
- 预处理 / 推理 / 后处理 分段耗时
- FPS（每秒处理帧数）
- 分 CPU 和 GPU 两个维度

**检测精度：**
- 无标注时：PT 与 ONNX 检测框 IoU 一致性
- 有标注时：mAP、各类别 AP、平均 IoU
- 置信度分布对比

**算力需求：**
- 模型参数量
- FLOPs（浮点运算次数）
- GPU/CPU 利用率

**资源占用：**
- 峰值内存占用（MB）
- 模型文件大小（MB）
- GPU 显存占用（MB）

### 8.3 图表展示

| 图表 | 类型 | 内容 |
|------|------|------|
| 推理速度 | 分组柱状图 | X 轴模型，Y 轴耗时，分组：预处理/推理/后处理，系列：CPU/GPU |
| 检测精度 | 雷达图 + 表格 | 多维度精度指标直观对比 |
| 资源占用 | 柱状图 | 峰值内存 + 模型大小 |
| 综合汇总 | 表格 | 所有指标汇总，支持导出 |

### 8.4 精度对比实现

1. 同一张图分别用 PT 和 ONNX 推理（相同预处理）
2. 对检测结果按类别分组，用匈牙利匹配算法配对框
3. 计算配对框的 IoU，统计平均 IoU 作为"精度一致性"指标
4. 如有标注文件（YOLO txt / COCO json），额外计算 mAP

## 9. 错误处理

### 9.1 统一错误响应格式

```json
{
  "success": false,
  "error_code": "MODEL_NOT_FOUND",
  "message": "模型 ID 3 不存在",
  "detail": null
}
```

### 9.2 错误场景处理

| 错误场景 | error_code | 处理方式 |
|---------|-----------|---------|
| 模型文件损坏/无法加载 | `MODEL_LOAD_ERROR` | 任务标记 failed，前端展示详情 |
| PT → ONNX 转换失败 | `CONVERT_FAILED` | 保留 PT，清除临时文件，记录日志 |
| GPU 不可用 | `GPU_UNAVAILABLE` | 自动降级 CPU，前端提示 |
| 文件上传超大 | `FILE_TOO_LARGE` | 限制 2GB，直接拒绝 |
| 推理过程中断 | `INFERENCE_INTERRUPTED` | 清理中间结果，任务可重试 |
| 磁盘空间不足 | `DISK_FULL` | 提前检查，拒绝操作 |

### 9.3 前端错误处理

- Axios 拦截器统一捕获 API 错误，`ElMessage` 提示
- 长任务轮询出错时展示错误状态，提供"重试"按钮
- 大文件上传支持进度展示和中断重试

## 10. 测试策略

| 层级 | 测试内容 | 工具 |
|------|---------|------|
| 后端单元测试 | 模型元数据提取、转换逻辑、引擎接口 | pytest |
| 后端 API 测试 | 各接口正常/异常流程 | pytest + httpx |
| 前端组件测试 | 关键表单、图表渲染、轮询逻辑 | Vitest + Vue Test Utils |
| 端到端测试 | 完整流程：上传 → 转换 → 推理 → 对比 | Playwright |
| 精度验证 | PT 和 ONNX 推理结果一致性（IoU > 0.95） | 自定义脚本 |
