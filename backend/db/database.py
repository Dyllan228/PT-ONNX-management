"""
数据库配置模块

本模块负责：
1. 创建 SQLAlchemy 数据库引擎
2. 配置数据库会话工厂
3. 定义数据库模型基类
4. 提供数据库依赖注入函数

技术栈：
- SQLAlchemy: Python SQL 工具包和 ORM 框架
- SQLite: 轻量级嵌入式数据库（默认）
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 数据库连接 URL
# 默认使用 SQLite，存储在 storage/benchmark.db
# 可通过环境变量 DATABASE_URL 切换到其他数据库（如 PostgreSQL）
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./storage/benchmark.db")

# 创建数据库引擎
# check_same_thread=False 是 SQLite 特有配置，允许多线程访问
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# 创建会话工厂
# autocommit=False: 不自动提交事务
# autoflush=False: 不自动刷新（手动控制何时写入数据库）
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明模型基类
# 所有数据库模型都继承这个类
Base = declarative_base()


def get_db():
    """
    数据库会话依赖注入函数

    用于 FastAPI 的 Depends()，每次请求创建一个独立的数据库会话
    请求结束后自动关闭会话，释放连接

    使用示例：
        @router.get("/api/models")
        def list_models(db: Session = Depends(get_db)):
            return db.query(Model).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    初始化数据库

    功能：
    1. 创建 storage 目录（如果不存在）
    2. 根据模型定义创建所有数据库表

    注意：已存在的表不会被修改或删除
    """
    os.makedirs("storage", exist_ok=True)
    Base.metadata.create_all(bind=engine)
