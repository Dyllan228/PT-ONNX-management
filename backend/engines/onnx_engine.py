"""
ONNX Runtime 推理引擎模块

本模块实现了 ONNX 模型的推理引擎，支持：
1. ONNX Runtime 推理
2. CPU/GPU 推理（CUDA）
3. 多输出模型支持
4. 实时性能统计

技术栈：
- ONNX Runtime: ONNX 模型推理框架
- OpenCV: 图像处理
- NumPy: 数值计算
"""

import onnxruntime as ort
import cv2
import numpy as np
import time


class ONNXEngine:
    """
    ONNX Runtime 推理引擎

    支持 YOLO 系列 ONNX 模型的推理

    使用示例：
        engine = ONNXEngine("yolov8n.onnx", device="cpu")
        engine.set_names({0: "helmet", 1: "vest"})
        detections, timings = engine.infer(image)
    """

    def __init__(self, model_path: str, device: str = "cpu"):
        """
        初始化 ONNX 推理引擎

        参数：
        - model_path: ONNX 模型文件路径
        - device: 推理设备（"cpu" 或 "cuda"）

        初始化过程：
        1. 检测可用的执行提供者（CPU/CUDA）
        2. 创建推理会话
        3. 分析模型输入输出结构
        """
        # 配置执行提供者（优先使用 GPU）
        providers = ["CUDAExecutionProvider"] if device == "cuda" else ["CPUExecutionProvider"]
        available = ort.get_available_providers()
        providers = [p for p in providers if p in available]
        if not providers:
            providers = ["CPUExecutionProvider"]

        # 创建推理会话
        self.session = ort.InferenceSession(model_path, providers=providers)
        # 获取输入名称
        self.input_name = self.session.get_inputs()[0].name
        # 记录实际使用的设备
        self.device = providers[0].replace("ExecutionProvider", "").lower()

        # 类别信息（需要通过 set_names 设置）
        self.names = {}
        self.nc = 0

        # 分析模型输出结构
        output_info = self.session.get_outputs()
        self.bbox_output_idx = 0   # 主输出索引（包含边界框）
        self.cls_output_idx = None  # 类别输出索引（如果独立）

        # 识别独立的类别 logits 输出
        for i, o in enumerate(output_info):
            if hasattr(o, 'shape') and len(o.shape) == 3:
                # 通过名称识别 Sigmoid 输出
                if 'Sigmoid' in o.name:
                    self.cls_output_idx = i

    def set_names(self, names: dict):
        """
        设置类别名称

        参数：
        - names: 类别名称字典，如 {0: "helmet", 1: "vest"}
        """
        self.names = names
        self.nc = len(names) if names else 0

    def preprocess(self, img: np.ndarray, input_size=(640, 640)):
        """
        图像预处理（ONNX 版本）

        处理步骤：
        1. Resize: 缩放到模型输入尺寸
        2. BGR→RGB: 颜色空间转换
        3. 归一化: 像素值从 [0, 255] 到 [0, 1]
        4. 转置: HWC → CHW
        5. 添加 batch 维度

        参数：
        - img: OpenCV 格式的图片（BGR）
        - input_size: 模型输入尺寸 (height, width)

        返回：
        - numpy.ndarray: 预处理后的数组 [1, C, H, W]
        """
        # 缩放到模型输入尺寸
        img_resized = cv2.resize(img, (input_size[1], input_size[0]))
        # BGR → RGB
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        # 归一化到 [0, 1]
        img_normalized = img_rgb.astype(np.float32) / 255.0
        # 转置：HWC → CHW，并添加 batch 维度
        img_tensor = np.transpose(img_normalized, (2, 0, 1))[np.newaxis, ...]
        return img_tensor

    def infer(self, img: np.ndarray, input_size=(640, 640), conf_threshold=0.5):
        """
        单图推理

        完整的推理流程：预处理 → 推理 → 后处理

        参数：
        - img: OpenCV 格式的图片（BGR）
        - input_size: 模型输入尺寸 (height, width)
        - conf_threshold: 置信度阈值

        返回：
        - detections: 检测结果列表
        - timings: 各阶段耗时（毫秒）
        """
        timings = {}

        # 预处理
        t0 = time.time()
        img_tensor = self.preprocess(img, input_size)
        timings["preprocess_ms"] = (time.time() - t0) * 1000

        # ONNX Runtime 推理
        t0 = time.time()
        outputs = self.session.run(None, {self.input_name: img_tensor})
        timings["inference_ms"] = (time.time() - t0) * 1000

        # 后处理
        t0 = time.time()
        detections = self._postprocess(outputs, img.shape, input_size, conf_threshold)
        timings["postprocess_ms"] = (time.time() - t0) * 1000

        return detections, timings

    def _postprocess(self, outputs, orig_shape, input_size, conf_threshold):
        """
        后处理：解析 ONNX 模型输出

        ONNX 导出的 YOLO 模型输出格式：
        - 主输出 [batch, 4+nc, N]: 边界框 + 类别 logits
        - 可能有独立的类别输出 [batch, nc, N]

        处理步骤：
        1. 解析输出结构
        2. 坐标转换：cx,cy,w,h → x1,y1,x2,y2
        3. Sigmoid 激活类别分数
        4. 过滤低置信度
        5. NMS
        6. 缩放到原图尺寸

        参数：
        - outputs: ONNX 模型输出列表
        - orig_shape: 原始图片尺寸
        - input_size: 模型输入尺寸
        - conf_threshold: 置信度阈值

        返回：
        - detections: 检测结果列表
        """
        h_orig, w_orig = orig_shape[:2]

        # 获取主输出（边界框）
        primary = outputs[self.bbox_output_idx]
        if primary.ndim == 3:
            # [batch, C, N] → [N, C]
            primary = primary[0].T
        elif primary.ndim == 2:
            if primary.shape[0] < primary.shape[1]:
                primary = primary.T

        # 解析边界框：cx, cy, w, h → x1, y1, x2, y2
        bbox_raw = primary[:, :4].copy()
        cx, cy = bbox_raw[:, 0], bbox_raw[:, 1]
        w, h = bbox_raw[:, 2], bbox_raw[:, 3]
        bboxes = np.stack([
            cx - w / 2,  # x1
            cy - h / 2,  # y1
            cx + w / 2,  # x2
            cy + h / 2   # y2
        ], axis=1)

        # 获取类别 logits（可能来自独立输出或主输出）
        if self.cls_output_idx is not None and self.cls_output_idx < len(outputs):
            cls_out = outputs[self.cls_output_idx]
            if cls_out.ndim == 3:
                cls_logits = cls_out[0].T  # [N, nc]
            elif cls_out.ndim == 2:
                cls_logits = cls_out if cls_out.shape[0] == bboxes.shape[0] else cls_out.T
            else:
                cls_logits = primary[:, 4:]
        else:
            cls_logits = primary[:, 4:]

        # 确定类别数量
        nc = self.nc if self.nc > 0 else cls_logits.shape[1]
        if nc <= 0:
            return []

        # Sigmoid 激活：将 logits 转换为概率
        cls_scores = 1.0 / (1.0 + np.exp(-cls_logits[:, :nc]))
        # 获取最高置信度和对应类别
        cls_conf = cls_scores.max(axis=1)
        cls_id = cls_scores.argmax(axis=1)

        # 过滤低置信度检测
        mask = cls_conf >= conf_threshold
        if not mask.any():
            return []

        bboxes = bboxes[mask]
        scores = cls_conf[mask]
        ids = cls_id[mask]

        # 非极大值抑制（NMS）
        keep = self._nms(bboxes, scores, iou_threshold=0.45)
        bboxes = bboxes[keep]
        scores = scores[keep]
        ids = ids[keep]

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
            cid = int(ids[i])
            detections.append({
                "class_id": cid,
                "class_name": self.names.get(cid, f"class_{cid}"),
                "confidence": float(scores[i]),
                "bbox": [float(v) for v in bboxes[i]],
            })

        return detections

    @staticmethod
    def _nms(bboxes, scores, iou_threshold=0.45):
        """
        非极大值抑制（NMS）

        参数：
        - bboxes: 边界框数组 [N, 4] (x1, y1, x2, y2)
        - scores: 置信度数组 [N]
        - iou_threshold: IoU 阈值

        返回：
        - keep: 保留的检测框索引列表
        """
        if len(bboxes) == 0:
            return []

        x1, y1, x2, y2 = bboxes[:, 0], bboxes[:, 1], bboxes[:, 2], bboxes[:, 3]
        areas = (x2 - x1) * (y2 - y1)
        order = scores.argsort()[::-1]
        keep = []

        while len(order) > 0:
            i = order[0]
            keep.append(i)
            if len(order) == 1:
                break

            # 计算 IoU
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
