"""
Kindle画面キャプチャ＆PDF生成パッケージ

Kindle for PCのウィンドウをキャプチャし、複数ページを結合してPDFを生成します。
"""

from kindle_capture.config import CaptureConfig
from kindle_capture.capture import KindleCaptureService
from kindle_capture.performance import PerformanceMonitor, PerformanceReport
from kindle_capture.exceptions import (
    KindleCaptureError,
    WindowNotFoundError,
    CaptureError,
    PDFGenerationError,
)

__version__ = "1.0.0"
__all__ = [
    "CaptureConfig",
    "KindleCaptureService",
    "PerformanceMonitor",
    "PerformanceReport",
    "KindleCaptureError",
    "WindowNotFoundError",
    "CaptureError",
    "PDFGenerationError",
]
