import torch
import cv2
import numpy as np
import time


class PTEngine:
    """PyTorch inference engine for YOLO-style detection models."""

    def __init__(self, model_path: str, device: str = "cpu"):
        self.device = torch.device(device if (device == "cpu" or torch.cuda.is_available()) else "cpu")
        checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)

        if isinstance(checkpoint, dict) and "model" in checkpoint:
            self.model = checkpoint["model"]
        elif hasattr(checkpoint, "model"):
            self.model = checkpoint.model
        else:
            self.model = checkpoint

        self.model.to(self.device)
        self.model.eval()

        if hasattr(checkpoint, "names"):
            self.names = checkpoint.names
        elif isinstance(checkpoint, dict) and "model" in checkpoint:
            m = checkpoint["model"]
            self.names = getattr(m, "names", {})
        else:
            self.names = {}

        if isinstance(self.names, list):
            self.names = {i: n for i, n in enumerate(self.names)}

    def preprocess(self, img: np.ndarray, input_size=(640, 640)):
        img_resized = cv2.resize(img, (input_size[1], input_size[0]))
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        img_normalized = img_rgb.astype(np.float32) / 255.0
        img_tensor = torch.from_numpy(img_normalized).permute(2, 0, 1).unsqueeze(0)
        return img_tensor.to(self.device)

    def infer(self, img: np.ndarray, input_size=(640, 640), conf_threshold=0.5):
        timings = {}

        t0 = time.time()
        img_tensor = self.preprocess(img, input_size)
        timings["preprocess_ms"] = (time.time() - t0) * 1000

        t0 = time.time()
        with torch.no_grad():
            outputs = self.model(img_tensor)
        timings["inference_ms"] = (time.time() - t0) * 1000

        t0 = time.time()
        detections = self._postprocess(outputs, img.shape, input_size, conf_threshold)
        timings["postprocess_ms"] = (time.time() - t0) * 1000

        return detections, timings

    def _postprocess(self, outputs, orig_shape, input_size, conf_threshold):
        detections = []
        h_orig, w_orig = orig_shape[:2]

        if isinstance(outputs, (list, tuple)):
            outputs = outputs[0]
        if isinstance(outputs, torch.Tensor):
            outputs = outputs.cpu().numpy()

        if len(outputs.shape) == 3:
            outputs = outputs[0]

        for det in outputs:
            if len(det) < 6:
                continue
            confidence = float(det[4])
            if confidence < conf_threshold:
                continue
            class_id = int(det[5]) if len(det) > 5 else 0
            x1 = float(det[0]) * w_orig / input_size[1]
            y1 = float(det[1]) * h_orig / input_size[0]
            x2 = float(det[2]) * w_orig / input_size[1]
            y2 = float(det[3]) * h_orig / input_size[0]

            detections.append({
                "class_id": class_id,
                "class_name": self.names.get(class_id, f"class_{class_id}"),
                "confidence": confidence,
                "bbox": [x1, y1, x2, y2],
            })

        return detections
