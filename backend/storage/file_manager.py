"""
文件管理模块

本模块负责管理项目中所有文件的存储路径，包括：
1. 模型文件（PT/ONNX）
2. 上传的媒体文件（图片/视频）
3. 推理结果文件
4. 数据集文件

目录结构：
storage/
├── models/
│   ├── pt/          # PyTorch 模型文件
│   └── onnx/        # ONNX 模型文件
├── uploads/
│   ├── images/      # 上传的图片
│   └── videos/      # 上传的视频
├── datasets/        # 导入的数据集
└── results/         # 推理结果
"""

from pathlib import Path

# ===== 项目路径配置 =====
# BASE_DIR: 项目根目录（backend 的上两级）
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# STORAGE_DIR: 数据存储根目录
STORAGE_DIR = BASE_DIR / "storage"

# 模型文件目录
MODELS_PT_DIR = STORAGE_DIR / "models" / "pt"      # PT 模型存储
MODELS_ONNX_DIR = STORAGE_DIR / "models" / "onnx"  # ONNX 模型存储

# 上传文件目录
UPLOADS_IMAGES_DIR = STORAGE_DIR / "uploads" / "images"  # 上传的图片
UPLOADS_VIDEOS_DIR = STORAGE_DIR / "uploads" / "videos"  # 上传的视频

# 结果文件目录
RESULTS_DIR = STORAGE_DIR / "results"  # 推理结果

# ===== 支持的文件格式 =====
SUPPORTED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}  # 支持的图片格式
SUPPORTED_VIDEO_EXT = {".mp4", ".avi", ".mov", ".mkv"}           # 支持的视频格式


def ensure_dirs():
    """
    确保所有必要的目录存在

    如果目录不存在则自动创建，包括：
    - 模型存储目录（PT/ONNX）
    - 上传文件目录（图片/视频）
    - 结果存储目录
    """
    for d in [MODELS_PT_DIR, MODELS_ONNX_DIR, UPLOADS_IMAGES_DIR,
              UPLOADS_VIDEOS_DIR, RESULTS_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def get_root_pt_files():
    """
    扫描项目根目录中的 .pt 模型文件

    用途：发现预先放置在项目根目录的模型文件，自动注册到系统

    返回：
    - list: .pt 文件路径列表
    """
    return list(BASE_DIR.glob("*.pt"))


def get_root_media_files():
    """
    扫描项目根目录中的媒体文件（图片/视频）

    用途：发现预先放置在项目根目录的测试数据

    返回：
    - list: 媒体文件路径列表
    """
    files = []
    for f in BASE_DIR.iterdir():
        if f.is_file() and f.suffix.lower() in SUPPORTED_IMAGE_EXT | SUPPORTED_VIDEO_EXT:
            files.append(f)
    return files
