"""
pytest設定と共通フィクスチャ
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# パッケージのインポートパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from kindle_capture.config import CaptureConfig


@pytest.fixture
def temp_dir():
    """一時ディレクトリを提供"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def test_config(temp_dir):
    """テスト用設定を提供"""
    return CaptureConfig(
        delay=0.1,
        similarity_threshold=0.99,
        max_pages=10,
        output_dir=temp_dir,
        activation_delay=0.01,
    )


@pytest.fixture
def mock_window_manager():
    """モック化されたWindowManagerを提供"""
    mock = MagicMock()
    mock.is_found = True
    mock.find_window.return_value = True
    mock.get_rect.return_value = (0, 0, 800, 600)
    mock.get_size.return_value = (800, 600)
    return mock


@pytest.fixture
def sample_image(temp_dir):
    """テスト用のサンプル画像を作成"""
    from PIL import Image
    
    img_path = os.path.join(temp_dir, "sample.png")
    img = Image.new("RGB", (100, 100), color="white")
    img.save(img_path)
    return img_path
