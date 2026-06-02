"""
PyTorch 推理引擎模块

本模块实现了 PyTorch 模型的推理引擎，支持：
1. Ultralytics YOLO 系列模型
2. 自动检测模型格式（Ultralytics/自定义）
3. CPU/GPU 推理
4. 实时性能统计

技术栈：
- PyTorch: 深度学习框架
- OpenCV: 图像处理
- NumPy: 数值计算
"""

import torch
import cv2
import numpy as np
import time


class PTEngine:
    """
    PyTorch 推理引擎

    支持 Ultralytics YOLO 系列模型的推理，包括：
    - YOLOv5
    - YOLOv8
    - YOLO11

    使用示例：
        engine = PTEngine("yolov8n.pt", device="cpu")
        detections, timings = engine.infer(image)
    """

    def __init__(self, model_path: str, device: str = "cpu"):
        """
        初始化推理引擎

        参数：
        - model_path: PT 模型文件路径
        - device: 推理设备（"cpu" 或 "cuda"）

        初始化过程：
        1. 检测设备可用性（CUDA）
        2. 加载模型文件
        3. 解析模型结构
        4. 提取类别名称
        5. 设置为评估模式
        """
        # 设置设备（自动回退到 CPU）
        self.device = torch.device(
            device if (device == "cpu" or torch.cuda.is_available()) else "cpu"
        )

        # 加载模型检查点
        checkpoint = torch.load(model_path, map_location="cpu", weights_only=False)

        # 解析模型结构（支持多种格式）
        if isinstance(checkpoint, dict) and "model" in checkpoint:
            # Ultralytics 格式：{"model": model_object, ...}
            self.model = checkpoint["model"]
        elif hasattr(checkpoint, "model"):
            # 对象格式：checkpoint.model
            self.model = checkpoint.model
        else:
            # 直接就是模型对象
            self.model = checkpoint

        # 设置模型为浮点型并移动到目标设备
        self.model.float().to(self.device)
        # 设置为评估模式（禁用 dropout、batchnorm 等训练特有的层）
        self.model.eval()

        # 提取类别名称
        self.names = {}
        if hasattr(self.model, "names"):
            raw_names = self.model.names
            if isinstance(raw_names, list):
                self.names = {i: n for i, n in enumerate(raw_names)}
            elif isinstance(raw_names, dict):
                self.names = {int(k): v for k, v in raw_names.items()}
        elif isinstance(checkpoint, dict) and "names" in checkpoint:
            raw_names = checkpoint["names"]
            if isinstance(raw_names, list):
                self.names = {i: n for i, n in enumerate(raw_names)}
            elif isinstance(raw_names, dict):
                self.names = {int(k): v for k, v in raw_names.items()}

        # 类别数量
        self.nc = len(self.names) if self.names else 0

    def preprocess(self, img: np.ndarray, input_size=(640, 640)):
        """
        图像预处理

        处理步骤：
        1. Resize: 缩放到模型输入尺寸
        2. BGR→RGB: 颜色空间转换
        3. 归一化: 像素值从 [0, 255] 到 [0, 1]
        4. 转 Tensor: numpy → torch.Tensor
        5. 添加 batch 维度: [C, H, W] → [1, C, H, W]

        参数：
        - img: OpenCV 格式的图片（BGR，numpy 数组）
        - input_size: 模型输入尺寸 (height, width)

        返回：
        - torch.Tensor: 预处理后的张量
        """
        # 缩放到模型输入尺寸
        img_resized = cv2.resize(img, (input_size[1], input_size[0]))
        # BGR → RGB（PyTorch 模型通常使用 RGB）
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        # 归一化到 [0, 1]
        img_normalized = img_rgb.astype(np.float32) / 255.0
        # 转换维度：HWC → CHW，并添加 batch 维度
        img_tensor = torch.from_numpy(img_normalized).permute(2, 0, 1).unsqueeze(0)
        return img_tensor.to(self.device)

    def infer(self, img: np.ndarray, input_size=(640, 640), conf_threshold=0.5):
        """
        单图推理

        完整的推理流程：预处理 → 推理 → 后处理

        参数：
        - img: OpenCV 格式的图片（BGR）
        - input_size: 模型输入尺寸 (height, width)
        - conf_threshold: 置信度阈值（低于此值的检测会被过滤）

        返回：
        - detections: 检测结果列表
        - timings: 各阶段耗时（毫秒）

        detection 格式：
        {
            "class_id": 类别 ID,
            "class_name": 类别名称,
            "confidence": 置信度,
            "bbox": [x1, y1, x2, y2]  # 边界框坐标
        }

        timings 格式：
        {
            "preprocess_ms": 预处理耗时,
            "inference_ms": 推理耗时,
            "postprocess_ms": 后处理耗时
        }
        """
        timings = {}

        # 预处理
        t0 = time.time()
        img_tensor = self.preprocess(img, input_size)
        timings["preprocess_ms"] = (time.time() - t0) * 1000

        # 推理（禁用梯度计算以节省内存）
        t0 = time.time()
        with torch.no_grad():
            outputs = self.model(img_tensor)
        timings["inference_ms"] = (time.time() - t0) * 1000

        # 后处理
        t0 = time.time()
        detections = self._postprocess(outputs, img.shape, input_size, conf_threshold)
        timings["postprocess_ms"] = (time.time() - t0) * 1000

        return detections, timings

    def _postprocess(self, outputs, orig_shape, input_size, conf_threshold):
        """
        后处理：解析模型输出为检测结果

        Ultralytics YOLO 模型输出格式：
        - 形状: [batch, 4+nc, num_anchors]
        - 前 4 通道: 已解码的 xyxy 坐标（在 input_size 空间）
        - 后 nc 通道: 已 sigmoid 的类别概率

        处理步骤：
        1. 统一输出格式
        2. 分离边界框和类别分数
        3. 坐标转换：cx,cy,w,h → x1,y1,x2,y2
        4. 过滤低置信度检测
        5. 非极大值抑制（NMS）
        6. 缩放到原图尺寸

        参数：
        - outputs: 模型原始输出
        - orig_shape: 原始图片尺寸 (H, W, C)
        - input_size: 模型输入尺寸 (H, W)
        - conf_threshold: 置信度阈值

        返回：
        - detections: 检测结果列表
        """
        h_orig, w_orig = orig_shape[:2]

        # 统一输出格式（可能是 list、tuple 或 tensor）
        if isinstance(outputs, (list, tuple)):
            outputs = outputs[0]
        if not isinstance(outputs, torch.Tensor):
            return []

        # 移动到 CPU 并分离梯度
        outputs = outputs.detach().cpu()

        # 去除 batch 维度: [1, C, N] → [C, N]
        if outputs.ndim == 3:
            outputs = outputs[0]
        elif outputs.ndim == 4:
            outputs = outputs[0]

        # 转置: [4+nc, N] → [N, 4+nc]（如果需要）
        if outputs.ndim == 2 and outputs.shape[0] < outputs.shape[1]:
            outputs = outputs.permute(1, 0)

        # 确定类别数量
        nc = self.nc if self.nc > 0 else outputs.shape[1] - 4
        if nc <= 0 or outputs.shape[1] < 4 + nc:
            return []

        # 分离边界框和类别分数
        bbox_raw = outputs[:, :4].numpy()          # [N, 4] cx, cy, w, h
        cls_scores = outputs[:, 4:4 + nc].numpy()  # [N, nc] 已 sigmoid

        # 坐标转换：cx, cy, w, h → x1, y1, x2, y2
        cx, cy = bbox_raw[:, 0], bbox_raw[:, 1]
        w, h = bbox_raw[:, 2], bbox_raw[:, 3]
        bboxes = np.stack([
            cx - w / 2,  # x1
            cy - h / 2,  # y1
            cx + w / 2,  # x2
            cy + h / 2   # y2
        ], axis=1)

        # 计算每个检测的置信度（最高类别概率）
        cls_conf = cls_scores.max(axis=1)
        cls_id = cls_scores.argmax(axis=1)

        # 过滤低置信度检测
        mask = cls_conf >= conf_threshold
        if not mask.any():
            return []

        bboxes = bboxes[mask]
        cls_conf = cls_conf[mask]
        cls_id = cls_id[mask]

        # 非极大值抑制（NMS）- 去除重叠的检测框
        keep = self._nms(bboxes, cls_conf, iou_threshold=0.45)
        bboxes = bboxes[keep]
        cls_conf = cls_conf[keep]
        cls_id = cls_id[keep]

        # 缩放到原图尺寸
        scale_x = w_orig / input_size[1]
        scale_y = h_orig / input_size[0]
        bboxes[:, [0, 2]] *= scale_x
        bboxes[:, [1, 3]] *= scale_y

        # 裁剪到图片范围内
        np.clip(bboxes[:, 0], 0, w_orig, out=bboxes[:, 0])
        np.clip(bboxes[:, 1], 0, h_orig, out=bboxes[:, 1])
        np.clip(bboxes[:, 2], 0, w_orig, out=bboxes[:, 2])
        np.clip(bboxes[:, 3], 0, h_orig, out=bboxes[:, 3])

        # 构建检测结果列表
        detections = []
        for i in range(len(bboxes)):
            cid = int(cls_id[i])
            detections.append({
                "class_id": cid,
                "class_name": self.names.get(cid, f"class_{cid}"),
                "confidence": float(cls_conf[i]),
                "bbox": [float(v) for v in bboxes[i]],
            })

        return detections

    @staticmethod
    def _nms(bboxes, scores, iou_threshold=0.45):
        """
        非极大值抑制（NMS）

        算法步骤：
        1. 按置信度降序排列所有检测框
        2. 选择置信度最高的框加入结果
        3. 删除与该框 IoU 大于阈值的其他框
        4. 重复直到处理完所有框

        参数：
        - bboxes: 边界框数组 [N, 4] (x1, y1, x2, y2)
        - scores: 置信度数组 [N]
        - iou_threshold: IoU 阈值（高于此值被认为是重复检测）

        返回：
        - keep: 保留的检测框索引列表
        """
        if len(bboxes) == 0:
            return []

        x1, y1, x2, y2 = bboxes[:, 0], bboxes[:, 1], bboxes[:, 2], bboxes[:, 3]
        areas = (x2 - x1) * (y2 - y1)

        # 按置信度降序排列
        order = scores.argsort()[::-1]
        keep = []

        while len(order) > 0:
            # 选择置信度最高的框
            i = order[0]
            keep.append(i)
            if len(order) == 1:
                break

            # 计算当前框与剩余框的 IoU
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])

            inter = np.maximum(0, xx2 - xx1) * np.maximum(0, yy2 - yy1)
            iou = inter / (areas[i] + areas[order[1:]] - inter)

            # 保留 IoU 小于阈值的框
            inds = np.where(iou <= iou_threshold)[0]
            if len(inds) == 0:
                break
            order = order[inds + 1]

        return keep

    def get_metrics(self):
        """
        获取模型元信息

        返回：
        - param_count: 模型参数量
        - names: 类别名称字典
        - device: 推理设备
        """
        param_count = sum(p.numel() for p in self.model.parameters())
        return {
            "param_count": param_count,
            "names": self.names,
            "device": str(self.device),
        }
