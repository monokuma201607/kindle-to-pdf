"""
ユニットテスト

各モジュールの単体テストを実装します。
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from kindle_capture.config import CaptureConfig
from kindle_capture.pdf_generator import PDFGenerator
from kindle_capture.exceptions import (
    WindowNotFoundError,
    PDFGenerationError,
    CaptureError,
)


class TestCaptureConfig:
    """CaptureConfigのテスト"""
    
    def test_default_values(self):
        """デフォルト値が正しく設定されること"""
        config = CaptureConfig()
        
        assert config.delay == 1.0
        assert config.similarity_threshold == 0.99
        assert config.max_pages == 9999
        assert "Kindle for PC" in config.window_keywords
    
    def test_custom_values(self):
        """カスタム値が正しく設定されること"""
        config = CaptureConfig(
            delay=2.0,
            similarity_threshold=0.95,
            max_pages=100,
        )
        
        assert config.delay == 2.0
        assert config.similarity_threshold == 0.95
        assert config.max_pages == 100
    
    def test_validation_delay_negative(self):
        """負のdelayでエラーになること"""
        with pytest.raises(ValueError):
            CaptureConfig(delay=-1.0)
    
    def test_validation_similarity_out_of_range(self):
        """範囲外のsimilarity_thresholdでエラーになること"""
        with pytest.raises(ValueError):
            CaptureConfig(similarity_threshold=1.5)
    
    def test_to_dict(self):
        """to_dictが正しい辞書を返すこと"""
        config = CaptureConfig(delay=2.0)
        result = config.to_dict()
        
        assert result["capture"]["delay"] == 2.0
        assert "output" in result
        assert "window" in result


class TestPDFGenerator:
    """PDFGeneratorのテスト"""
    
    def test_generate_single_image(self, temp_dir, sample_image):
        """単一画像からPDFを生成できること"""
        generator = PDFGenerator(temp_dir)
        pdf_path = generator.generate([sample_image], "test.pdf")
        
        assert os.path.exists(pdf_path)
        assert pdf_path.endswith("test.pdf")
    
    def test_generate_multiple_images(self, temp_dir):
        """複数画像からPDFを生成できること"""
        # 複数のテスト画像を作成
        images = []
        for i in range(3):
            img_path = os.path.join(temp_dir, f"img_{i}.png")
            img = Image.new("RGB", (100, 100), color=(i * 50, 100, 100))
            img.save(img_path)
            images.append(img_path)
        
        generator = PDFGenerator(temp_dir)
        pdf_path = generator.generate(images, "multi.pdf")
        
        assert os.path.exists(pdf_path)
    
    def test_generate_empty_list_raises_error(self, temp_dir):
        """空のリストでエラーになること"""
        generator = PDFGenerator(temp_dir)
        
        with pytest.raises(PDFGenerationError):
            generator.generate([], "empty.pdf")


class TestExceptions:
    """例外クラスのテスト"""
    
    def test_window_not_found_error(self):
        """WindowNotFoundErrorのメッセージ"""
        error = WindowNotFoundError()
        assert "見つかりません" in str(error)
    
    def test_pdf_generation_error_custom_message(self):
        """カスタムメッセージが設定されること"""
        error = PDFGenerationError("カスタムエラー")
        assert "カスタムエラー" in str(error)
