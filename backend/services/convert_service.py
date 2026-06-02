"""
模型转换服务模块

本模块提供 PyTorch 模型到 ONNX 格式的转换功能，包括：
1. 加载 PyTorch 模型
2. 配置导出参数
3. 执行 ONNX 导出
4. 更新数据库状态

技术栈：
- PyTorch: 模型加载和导出
- ONNX: 模型格式标准

注意事项：
- 在后台线程运行，需要独立的数据库会话
- 实时更新进度到数据库
- 支持动态 Batch 和自定义 Opset 版本
"""

import torch
from pathlib import Path
from db.database import SessionLocal
from db.models import Model as ModelDB, Task
from storage.file_manager import MODELS_ONNX_DIR


def convert_pt_to_onnx(model_id: int, task_id: str,
                       input_size=(640, 640), opset_version=11, dynamic_batch=True):
    """
    将 PyTorch 模型转换为 ONNX 格式

    转换流程：
    1. 创建独立的数据库会话（后台线程）
    2. 加载 PyTorch 模型
    3. 准备虚拟输入
    4. 执行 ONNX 导出
    5. 更新模型状态

    参数：
    - model_id: 模型 ID
    - task_id: 任务 ID
    - input_size: 输入尺寸 (height, width)，默认 (640, 640)
    - opset_version: ONNX Opset 版本，默认 11
    - dynamic_batch: 是否支持动态 Batch，默认 True

    ONNX Opset 版本说明：
    - 11: 兼容性好，推荐使用
    - 12-13: 支持更多算子
    - 14+: 最新特性，但需要更新的运行时
    """
    # 创建独立的数据库会话（后台线程不能使用主会话）
    db = SessionLocal()
    try:
        # 获取模型和任务记录
        model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
        task = db.query(Task).filter(Task.id == task_id).first()

        # 更新任务状态
        task.status = "running"
        task.progress = 10
        db.commit()

        # 加载 PyTorch 模型
        checkpoint = torch.load(model.pt_file_path, map_location="cpu", weights_only=False)
        task.progress = 30
        db.commit()

        # 解析模型结构
        if isinstance(checkpoint, dict) and "model" in checkpoint:
            pt_model = checkpoint["model"]
        elif hasattr(checkpoint, "model"):
            pt_model = checkpoint.model
        else:
            pt_model = checkpoint

        # 设置为浮点型和评估模式
        pt_model.float().eval()
        task.progress = 50
        db.commit()

        # 创建虚拟输入（ONNX 导出需要）
        dummy_input = torch.randn(1, 3, input_size[0], input_size[1])

        # 确定输出路径
        pt_path = Path(model.pt_file_path)
        onnx_filename = pt_path.stem + ".onnx"
        onnx_path = MODELS_ONNX_DIR / onnx_filename
        onnx_path.parent.mkdir(parents=True, exist_ok=True)

        task.progress = 60
        db.commit()

        # 配置动态轴（如果启用动态 Batch）
        dynamic_axes = None
        if dynamic_batch:
            dynamic_axes = {
                "input": {0: "batch_size"},
                "output": {0: "batch_size"}
            }

        # 执行 ONNX 导出
        torch.onnx.export(
            pt_model,                    # 模型
            dummy_input,                 # 虚拟输入
            str(onnx_path),              # 输出路径
            opset_version=opset_version, # Opset 版本
            input_names=["input"],       # 输入名称
            output_names=["output"],     # 输出名称
            dynamic_axes=dynamic_axes,   # 动态轴配置
        )

        task.progress = 90
        db.commit()

        # 更新模型状态
        model.onnx_file_path = str(onnx_path)
        model.onnx_converted = True
        model.onnx_file_size = onnx_path.stat().st_size

        # 更新任务状态为完成
        task.progress = 100
        task.status = "completed"
        task.result = {
            "onnx_path": str(onnx_path),
            "file_size": model.onnx_file_size
        }
        db.commit()

    except Exception as e:
        # 更新任务状态为失败
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = "failed"
            task.error_msg = str(e)
            db.commit()
    finally:
        # 关闭数据库会话
        db.close()
