"""OCR 文字识别模块（基于 OpenCV + 规则提取体检指标）"""

import re
import cv2
import numpy as np

# 常见体检指标的关键词及单位
INDICATOR_PATTERNS = {
    "收缩压":   r"收缩压[：:]?\s*(\d{2,3})\s*(?:mmHg|毫米汞柱)?",
    "舒张压":   r"舒张压[：:]?\s*(\d{2,3})\s*(?:mmHg|毫米汞柱)?",
    "空腹血糖": r"空腹血糖[：:]?\s*(\d+\.?\d*)\s*(?:mmol/L)?",
    "总胆固醇": r"(?:总胆固醇|TC)[：:]?\s*(\d+\.?\d*)\s*(?:mmol/L)?",
    "甘油三酯": r"(?:甘油三酯|TG)[：:]?\s*(\d+\.?\d*)\s*(?:mmol/L)?",
    "高密度脂蛋白": r"(?:高密度脂蛋白|HDL)[：:]?\s*(\d+\.?\d*)\s*(?:mmol/L)?",
    "低密度脂蛋白": r"(?:低密度脂蛋白|LDL)[：:]?\s*(\d+\.?\d*)\s*(?:mmol/L)?",
    "尿酸":     r"尿酸[：:]?\s*(\d+\.?\d*)\s*(?:umol/L|μmol/L)?",
    "肌酐":     r"肌酐[：:]?\s*(\d+\.?\d*)\s*(?:umol/L|μmol/L)?",
    "谷丙转氨酶": r"(?:谷丙转氨酶|ALT)[：:]?\s*(\d+\.?\d*)\s*(?:U/L)?",
    "谷草转氨酶": r"(?:谷草转氨酶|AST)[：:]?\s*(\d+\.?\d*)\s*(?:U/L)?",
    "白细胞计数": r"(?:白细胞|WBC)[：:]?\s*(\d+\.?\d*)\s*(?:×10\^?9/L)?",
    "红细胞计数": r"(?:红细胞|RBC)[：:]?\s*(\d+\.?\d*)\s*(?:×10\^?12/L)?",
    "血红蛋白":  r"(?:血红蛋白|Hb|HGB)[：:]?\s*(\d+\.?\d*)\s*(?:g/L)?",
    "血小板计数": r"(?:血小板|PLT)[：:]?\s*(\d+\.?\d*)\s*(?:×10\^?9/L)?",
}


def preprocess(image_bytes: bytes) -> np.ndarray:
    """图像预处理：灰度化 → 高斯去噪 → 自适应二值化"""
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("无法解析图片")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.GaussianBlur(gray, (5, 5), 0)
    binary = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 11, 2)
    return binary


def extract_indicators(text: str) -> dict:
    """从 OCR 文本中提取体检指标数值"""
    result = {}
    for name, pattern in INDICATOR_PATTERNS.items():
        match = re.search(pattern, text)
        if match:
            try:
                result[name] = float(match.group(1))
            except ValueError:
                result[name] = match.group(1)
    return result


def recognize(image_bytes: bytes) -> dict:
    """
    模拟 OCR 识别流程（生产环境可接入 PaddleOCR / Tesseract）
    当前返回预处理的图像尺寸信息 + 模拟提取
    """
    binary = preprocess(image_bytes)

    # 模拟识别文本（生产环境替换为 OCR 引擎）
    # 此处演示：基于 OpenCV 轮廓检测模拟区域提取
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    return {
        "image_width": binary.shape[1],
        "image_height": binary.shape[0],
        "text_regions_detected": min(len(contours), 200),
        "engine": "opencv-contour-simulated",
    }


def recognize_and_extract(image_bytes: bytes, simulated_text: str | None = None) -> dict:
    """
    综合 OCR 识别流程：
    1. 图像预处理 + 区域检测
    2. 文本提取（生产环境接入真实 OCR 引擎，当前支持模拟文本）
    3. 指标正则提取
    """
    meta = recognize(image_bytes)

    if simulated_text:
        indicators = extract_indicators(simulated_text)
    else:
        indicators = {}

    meta["indicators"] = indicators
    meta["indicator_count"] = len(indicators)
    return meta
