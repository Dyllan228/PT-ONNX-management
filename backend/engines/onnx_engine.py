import onnxruntime as ort
import cv2
import numpy as np
import time


class ONNXEngine:
    """ONNX Runtime inference engine for detection models."""

    def __init__(self, model_path: str, device: str = "cpu"):
        providers = ["CUDAExecutionProvider"] if device == "cuda" else ["CPUExecutionProvider"]
        available = ort.get_available_providers()
        providers = [p for p in providers if p in available]
        if not providers:
            providers = ["CPUExecutionProvider"]

        self.session = ort.InferenceSession(model_path, providers=providers)
        self.input_name = self.session.get_inputs()[0].name
        self.output_names = [o.name for o in self.session.get_outputs()]
        self.device = providers[0].replace("ExecutionProvider", "").lower()
        self.names = {}

    def set_names(self, names: dict):
        self.names = names

    def preprocess(self, img: np.ndarray, input_size=(640, 640)):
        img_resized = cv2.resize(img, (input_size[1], input_size[0]))
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        img_normalized = img_rgb.astype(np.float32) / 255.0
        img_tensor = np.transpose(img_normalized, (2, 0, 1))[np.newaxis, ...]
        return img_tensor

    def infer(self, img: np.ndarray, input_size=(640, 640), conf_threshold=0.5):
        timings = {}

        t0 = time.time()
        img_tensor = self.preprocess(img, input_size)
        timings["preprocess_ms"] = (time.time() - t0) * 1000

        t0 = time.time()
        outputs = self.session.run(self.output_names, {self.input_name: img_tensor})
        timings["inference_ms"] = (time.time() - t0) * 1000

        t0 = time.time()
        detections = self._postprocess(outputs, img.shape, input_size, conf_threshold)
        timings["postprocess_ms"] = (time.time() - t0) * 1000

        return detections, timings

    def _postprocess(self, outputs, orig_shape, input_size, conf_threshold):
        detections = []
        h_orig, w_orig = orig_shape[:2]
        output = outputs[0]

        if len(output.shape) == 3:
            output = output[0]

        for det in output:
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
