"""
パフォーマンステスト

キャプチャ・PDF生成のパフォーマンスを測定・検証します。
"""

import os
import time
import tempfile
from pathlib import Path

import pytest
from PIL import Image

from kindle_capture.config import CaptureConfig
from kindle_capture.pdf_generator import PDFGenerator
from kindle_capture.performance import (
    PerformanceMonitor,
    PerformanceReport,
    TimingResult,
)


class TestPerformanceMonitor:
    """PerformanceMonitorのテスト"""
    
    def test_measure_context_manager(self):
        """measureコンテキストマネージャが正しく計測すること"""
        monitor = PerformanceMonitor()
        monitor.start_session()
        
        with monitor.measure("test_operation"):
            time.sleep(0.1)
        
        monitor.end_session()
        report = monitor.get_report()
        
        assert len(report.timings) == 1
        assert report.timings[0].name == "test_operation"
        assert 0.09 <= report.timings[0].duration <= 0.2
    
    def test_multiple_measurements(self):
        """複数の計測が正しく記録されること"""
        monitor = PerformanceMonitor()
        monitor.start_session()
        
        with monitor.measure("op1"):
            time.sleep(0.05)
        
        with monitor.measure("op2"):
            time.sleep(0.05)
        
        monitor.end_session(page_count=2)
        report = monitor.get_report()
        
        assert len(report.timings) == 2
        assert report.page_count == 2
    
    def test_timer_start_stop(self):
        """start_timer/stop_timerが正しく動作すること"""
        monitor = PerformanceMonitor()
        monitor.start_session()
        
        monitor.start_timer("manual_timer")
        time.sleep(0.05)
        monitor.stop_timer()
        
        report = monitor.get_report()
        assert len(report.timings) == 1
        assert report.timings[0].name == "manual_timer"


class TestPerformanceReport:
    """PerformanceReportのテスト"""
    
    def test_total_duration(self):
        """総時間が正しく計算されること"""
        report = PerformanceReport(
            timings=[
                TimingResult("op1", 0.0, 1.0),
                TimingResult("op2", 1.0, 2.5),
            ],
            page_count=5
        )
        
        assert report.total_duration == 2.5
    
    def test_avg_page_time(self):
        """ページ平均時間が正しく計算されること"""
        report = PerformanceReport(
            timings=[TimingResult("all", 0.0, 10.0)],
            page_count=10
        )
        
        assert report.avg_page_time == 1.0
    
    def test_avg_page_time_zero_pages(self):
        """ページ数0でもエラーにならないこと"""
        report = PerformanceReport(page_count=0)
        assert report.avg_page_time == 0
    
    def test_summary_format(self):
        """サマリーが正しい形式で生成されること"""
        report = PerformanceReport(
            timings=[TimingResult("test", 0.0, 1.0)],
            page_count=1
        )
        
        summary = report.summary()
        assert "パフォーマンスレポート" in summary
        assert "test" in summary


class TestTimingResult:
    """TimingResultのテスト"""
    
    def test_duration(self):
        """durationが正しく計算されること"""
        result = TimingResult("test", 0.0, 1.5)
        assert result.duration == 1.5
    
    def test_duration_ms(self):
        """duration_msが正しく計算されること"""
        result = TimingResult("test", 0.0, 0.5)
        assert result.duration_ms == 500.0


class TestPDFGenerationPerformance:
    """PDF生成のパフォーマンステスト"""
    
    @pytest.fixture
    def temp_images(self, temp_dir):
        """テスト用の複数画像を生成"""
        images = []
        for i in range(10):
            path = os.path.join(temp_dir, f"page_{i:03d}.png")
            img = Image.new("RGB", (800, 600), color=(i * 20, 100, 100))
            img.save(path)
            images.append(path)
        return images
    
    def test_pdf_generation_time(self, temp_dir, temp_images):
        """PDF生成が3秒以内に完了すること（10ページ）"""
        generator = PDFGenerator(temp_dir)
        
        start = time.perf_counter()
        pdf_path = generator.generate(temp_images, "perf_test.pdf")
        duration = time.perf_counter() - start
        
        assert os.path.exists(pdf_path)
        assert duration < 3.0, f"PDF生成に{duration:.2f}秒かかりました（3秒以内が目標）"
    
    def test_pdf_generation_per_page_time(self, temp_dir, temp_images):
        """ページあたりの生成時間が200ms以内であること"""
        generator = PDFGenerator(temp_dir)
        
        start = time.perf_counter()
        generator.generate(temp_images, "perf_test2.pdf")
        duration = time.perf_counter() - start
        
        per_page_time = duration / len(temp_images)
        assert per_page_time < 0.2, f"ページあたり{per_page_time*1000:.1f}msかかりました"


class TestImageComparisonPerformance:
    """画像比較のパフォーマンステスト"""
    
    def test_image_comparison_time(self, temp_dir):
        """画像比較が100ms以内に完了すること"""
        # テスト画像を作成
        img1_path = os.path.join(temp_dir, "img1.png")
        img2_path = os.path.join(temp_dir, "img2.png")
        
        img1 = Image.new("RGB", (800, 600), color="white")
        img1.save(img1_path)
        
        img2 = Image.new("RGB", (800, 600), color="white")
        img2.putpixel((100, 100), (255, 0, 0))  # 1ピクセルだけ異なる
        img2.save(img2_path)
        
        from kindle_capture.capture import ScreenCapture
        from kindle_capture.window import WindowManager
        
        config = CaptureConfig()
        window = WindowManager(config.window_keywords)
        capture = ScreenCapture(window, config)
        
        start = time.perf_counter()
        similarity = capture.compare_images(img1_path, img2_path)
        duration = time.perf_counter() - start
        
        assert duration < 0.5, f"画像比較に{duration*1000:.1f}msかかりました"
        assert similarity > 0.99  # ほぼ同じ


class TestConfigPerformance:
    """設定読み込みのパフォーマンステスト"""
    
    def test_config_load_time(self, temp_dir):
        """設定ファイル読み込みが50ms以内に完了すること"""
        # テスト用設定ファイル作成
        config_path = os.path.join(temp_dir, "test_config.yaml")
        with open(config_path, "w") as f:
            f.write("capture:\n  delay: 0.5\n")
        
        start = time.perf_counter()
        config = CaptureConfig.from_yaml(config_path)
        duration = time.perf_counter() - start
        
        assert duration < 0.2, f"設定読み込みに{duration*1000:.1f}msかかりました"
        assert config.delay == 0.5
