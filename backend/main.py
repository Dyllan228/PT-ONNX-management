"""
PT-ONNX Benchmark Tool v2.0 - 主入口文件

本文件是 FastAPI 应用的入口点，负责：
1. 配置应用生命周期（启动时初始化数据库和扫描模型）
2. 设置 CORS 中间件（允许跨域请求）
3. 注册所有 API 路由
4. 配置静态文件托管（生产模式）

技术栈：
- FastAPI: 高性能异步 Web 框架
- Uvicorn: ASGI 服务器
- SQLAlchemy: ORM 数据库操作
"""

import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from db.database import init_db
from api.models import router as models_router
from api.convert import router as convert_router
from api.tasks import router as tasks_router
from api.inference import router as inference_router
from api.benchmark import router as benchmark_router
from api.datasets import router as datasets_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理器

    功能：
    - 启动时：初始化数据库表结构，自动扫描并注册新模型
    - 关闭时：可选的清理操作

    使用 asynccontextmanager 实现异步上下文管理
    """
    # ===== 启动阶段 =====
    # 初始化数据库（创建表结构）
    init_db()

    # 自动扫描项目目录中的 .pt 模型文件并注册到数据库
    from services.scan_service import scan_and_register
    from db.database import SessionLocal
    db = SessionLocal()
    try:
        count = scan_and_register(db)
        print(f"自动扫描: 注册了 {count} 个新模型")
    finally:
        db.close()

    yield  # 应用运行期间

    # ===== 关闭阶段（如需要可添加清理逻辑） =====


# 创建 FastAPI 应用实例
app = FastAPI(
    title="PT-ONNX Benchmark Tool",  # API 文档标题
    version="2.0.0",                   # 版本号
    lifespan=lifespan                  # 生命周期管理
)

# ===== CORS 中间件配置 =====
# 允许前端开发服务器（localhost:5173）进行跨域请求
# 生产模式下前后端同源，不需要 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",    # Vite 开发服务器
        "http://127.0.0.1:5173",
        "*"                         # 开发阶段允许所有来源
    ],
    allow_credentials=True,   # 允许携带认证信息
    allow_methods=["*"],      # 允许所有 HTTP 方法
    allow_headers=["*"],      # 允许所有请求头
)

# ===== 注册 API 路由 =====
# 每个路由模块处理特定的业务功能
app.include_router(models_router)      # 模型管理 API（CRUD、上传、扫描）
app.include_router(convert_router)     # 模型转换 API（PT → ONNX）
app.include_router(tasks_router)       # 任务管理 API（查询、删除任务）
app.include_router(inference_router)   # 推理可视化 API（图片/视频推理）
app.include_router(benchmark_router)   # 性能对比 API（速度、准确度测试）
app.include_router(datasets_router)    # 数据集管理 API（导入、分析、下载）


@app.get("/api/health")
def health_check():
    """
    健康检查接口

    用途：
    - 监控服务是否正常运行
    - Docker 容器健康检查
    - 负载均衡器探针

    返回：
    - status: 服务状态
    - version: 应用版本号
    """
    return {"status": "ok", "version": "2.0.0"}


# ====== 生产模式：托管前端静态文件 ======
# 前端 build 后的文件位于 backend/../frontend/dist
# 这样前后端可以部署在同一个服务器上，无需单独的 Web 服务器
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists():
    print(f"[INFO] 前端构建文件已找到: {FRONTEND_DIST}")

    # 挂载静态资源目录（JS/CSS/图片等）
    # 这些文件会被直接提供，不经过 FastAPI 路由
    app.mount(
        "/assets",
        StaticFiles(directory=str(FRONTEND_DIST / "assets")),
        name="static-assets"
    )

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """
        SPA（单页应用）路由回退

        工作原理：
        1. 如果请求的是真实文件（如 /assets/index.js），直接返回
        2. 否则返回 index.html，让前端路由处理（如 /models、/inference）

        这是 SPA 应用的标准部署模式，支持前端路由（History Mode）
        """
        file_path = FRONTEND_DIST / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        # 非文件请求都返回 index.html，由前端路由处理
        return FileResponse(str(FRONTEND_DIST / "index.html"))
else:
    print(f"[WARN] 前端构建文件未找到: {FRONTEND_DIST}")
    print("[WARN] 生产模式已禁用。请先在 frontend/ 目录执行 'npm run build'")


# ====== 启动入口 ======
if __name__ == "__main__":
    import uvicorn

    print("=" * 50)
    print("  PT-ONNX Benchmark Tool v2.0")
    print("  URL: http://localhost:8000")
    print("=" * 50)

    # 启动 Uvicorn ASGI 服务器
    # host="0.0.0.0" 表示监听所有网络接口（允许外部访问）
    # port=8000 是默认端口
    uvicorn.run(app, host="0.0.0.0", port=8000)
