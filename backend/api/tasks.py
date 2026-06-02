"""
任务管理 API 模块

本模块提供异步任务的通用管理功能，包括：
1. 查询任意类型任务的状态
2. 删除任务记录

路由前缀：/api/tasks

注意：此模块是通用任务查询接口，具体业务逻辑在各业务模块中实现
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import Task

# 创建路由器
router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("/{task_id}")
def get_task(task_id: str, db: Session = Depends(get_db)):
    """
    查询任务状态（通用接口）

    可查询任意类型的任务：convert、inference、benchmark

    参数：
    - task_id: 任务 ID

    返回：
    - task_id: 任务 ID
    - type: 任务类型（convert/inference/benchmark）
    - status: 任务状态（pending/running/completed/failed）
    - progress: 进度百分比（0-100）
    - params: 任务参数
    - result: 任务结果
    - error_msg: 错误信息
    - created_at: 创建时间
    - finished_at: 完成时间

    异常：
    - 404: 任务不存在
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "task_id": task.id,
        "type": task.type,
        "status": task.status,
        "progress": task.progress,
        "params": task.params,
        "result": task.result,
        "error_msg": task.error_msg,
        "created_at": str(task.created_at) if task.created_at else None,
        "finished_at": str(task.finished_at) if task.finished_at else None,
    }


@router.delete("/{task_id}")
def delete_task(task_id: str, db: Session = Depends(get_db)):
    """
    删除任务记录

    注意：仅删除数据库记录，不会停止正在运行的任务

    参数：
    - task_id: 任务 ID

    返回：
    - dict: {"success": true}

    异常：
    - 404: 任务不存在
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"success": True}
