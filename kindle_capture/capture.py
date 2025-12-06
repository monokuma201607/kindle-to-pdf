"""
画面キャプチャモジュール

画面のキャプチャ、画像比較、ページ遷移を担当します。
"""

import os
import time
import shutil
import tempfile
import logging
from pathlib import Path
from typing import List, Optional, Callable, Tuple

import pyautogui
from PIL import Image

from kindle_capture.config import CaptureConfig
from kindle_capture.window import WindowManager
from kindle_capture.pdf_generator import PDFGenerator
from kindle_capture.exceptions import CaptureError, WindowNotFoundError
from kindle_capture.performance import PerformanceMonitor, PerformanceReport

logger = logging.getLogger(__name__)


class ScreenCapture:
    """画面キャプチャを実行するクラス"""
    
    def __init__(self, window_manager: WindowManager, config: CaptureConfig):
        """
        初期化
        
        Args:
            window_manager: ウィンドウ管理オブジェクト
            config: キャプチャ設定
        """
        self._window = window_manager
        self._config = config
        self._temp_dir: Optional[str] = None
    
    def capture_window(self, save_path: str) -> bool:
        """
        ウィンドウをキャプチャして保存
        
        Args:
            save_path: 保存先パス
            
        Returns:
            成功した場合True
        """
        rect = self._window.get_rect()
        if not rect:
            logger.error("ウィンドウ座標を取得できません")
            return False
        
        left, top, right, bottom = rect
        
        # マージンを適用（UI要素をトリミング）
        left += self._config.margin_left
        top += self._config.margin_top
        right -= self._config.margin_right
        bottom -= self._config.margin_bottom
        
        width = right - left
        height = bottom - top
        
        if width <= 0 or height <= 0:
            logger.error("マージン設定が大きすぎます")
            return False
        
        try:
            screenshot = pyautogui.screenshot(region=(left, top, width, height))
            screenshot.save(save_path)
            logger.debug(f"キャプチャ保存: {save_path} (サイズ: {width}x{height})")
            return True
        except Exception as e:
            logger.error(f"キャプチャエラー: {e}")
            return False
    
    def compare_images(self, img1_path: str, img2_path: str) -> float:
        """
        2つの画像の類似度を計算
        
        Args:
            img1_path: 画像1のパス
            img2_path: 画像2のパス
            
        Returns:
            類似度（0.0〜1.0、1.0は完全一致）
        """
        try:
            img1 = Image.open(img1_path)
            img2 = Image.open(img2_path)
            
            if img1.size != img2.size:
                return 0.0
            
            pixels1 = list(img1.getdata())
            pixels2 = list(img2.getdata())
            
            if len(pixels1) != len(pixels2):
                return 0.0
            
            matches = sum(1 for p1, p2 in zip(pixels1, pixels2) if p1 == p2)
            similarity = matches / len(pixels1)
            logger.debug(f"画像類似度: {similarity:.2%}")
            return similarity
            
        except Exception as e:
            logger.error(f"画像比較エラー: {e}")
            return 0.0
    
    @staticmethod
    def next_page() -> None:
        """次のページへ遷移"""
        pyautogui.press('right')
        logger.debug("次ページへ遷移")
    
    @staticmethod
    def previous_page() -> None:
        """前のページへ遷移"""
        pyautogui.press('left')
        logger.debug("前ページへ遷移")
    
    def _create_temp_dir(self) -> str:
        """一時ディレクトリを作成"""
        self._temp_dir = tempfile.mkdtemp(prefix="kindle_capture_")
        logger.debug(f"一時ディレクトリ作成: {self._temp_dir}")
        return self._temp_dir
    
    def cleanup(self) -> None:
        """一時ファイルを削除"""
        if self._temp_dir and os.path.exists(self._temp_dir):
            try:
                shutil.rmtree(self._temp_dir)
                logger.info("一時ファイルを削除しました")
            except Exception as e:
                logger.error(f"一時ファイル削除エラー: {e}")
            self._temp_dir = None
    
    def capture_pages(
        self,
        num_pages: int,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[str]:
        """
        指定ページ数をキャプチャ
        
        Args:
            num_pages: キャプチャするページ数
            progress_callback: 進捗コールバック (current, total) -> None
            
        Returns:
            キャプチャした画像ファイルパスのリスト
        """
        self._window.ensure_found()
        self._window.activate()
        self._create_temp_dir()
        
        captured_files: List[str] = []
        logger.info(f"キャプチャ開始: {num_pages}ページ")
        time.sleep(0.5)
        
        for i in range(num_pages):
            if progress_callback:
                progress_callback(i + 1, num_pages)
            
            file_path = os.path.join(self._temp_dir, f"page_{i:04d}.png")
            if self.capture_window(file_path):
                captured_files.append(file_path)
            else:
                logger.warning(f"ページ {i + 1} のキャプチャに失敗")
            
            if i < num_pages - 1:
                self.next_page()
                time.sleep(self._config.delay)
        
        logger.info(f"キャプチャ完了: {len(captured_files)}ページ")
        return captured_files
    
    def capture_all_pages(
        self,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> List[str]:
        """
        最後のページまで自動でキャプチャ
        
        Args:
            progress_callback: 進捗コールバック (current) -> None
            
        Returns:
            キャプチャした画像ファイルパスのリスト
        """
        self._window.ensure_found()
        self._window.activate()
        self._create_temp_dir()
        
        captured_files: List[str] = []
        consecutive_duplicates = 0
        last_image_path: Optional[str] = None
        
        logger.info(f"自動キャプチャ開始（最大: {self._config.max_pages}ページ）")
        time.sleep(0.5)
        
        for i in range(self._config.max_pages):
            if progress_callback:
                progress_callback(i + 1)
            
            file_path = os.path.join(self._temp_dir, f"page_{i:04d}.png")
            if not self.capture_window(file_path):
                logger.warning(f"ページ {i + 1} のキャプチャに失敗")
                continue
            
            # 重複検出
            if last_image_path:
                similarity = self.compare_images(last_image_path, file_path)
                if similarity >= self._config.similarity_threshold:
                    consecutive_duplicates += 1
                    logger.info(f"最後のページを検出（類似度: {similarity:.2%}）")
                    os.remove(file_path)
                    if consecutive_duplicates >= 2:
                        logger.info("連続して同じページを検出したため停止")
                        break
                else:
                    consecutive_duplicates = 0
                    captured_files.append(file_path)
                    last_image_path = file_path
            else:
                captured_files.append(file_path)
                last_image_path = file_path
            
            self.next_page()
            time.sleep(self._config.delay)
        
        logger.info(f"キャプチャ完了: {len(captured_files)}ページ")
        return captured_files


class KindleCaptureService:
    """
    Kindleキャプチャサービス
    
    ウィンドウ操作、キャプチャ、PDF生成を統合したファサードクラス
    """
    
    def __init__(self, config: Optional[CaptureConfig] = None):
        """
        初期化
        
        Args:
            config: キャプチャ設定（省略時はデフォルト設定）
        """
        self._config = config or CaptureConfig()
        self._window = WindowManager(
            keywords=self._config.window_keywords,
            activation_delay=self._config.activation_delay
        )
        self._capture = ScreenCapture(self._window, self._config)
        self._pdf = PDFGenerator(self._config.output_dir)
        self._perf = PerformanceMonitor()
        self._last_report: Optional[PerformanceReport] = None
    
    @property
    def config(self) -> CaptureConfig:
        """現在の設定を取得"""
        return self._config
    
    @property
    def window(self) -> WindowManager:
        """ウィンドウマネージャを取得"""
        return self._window
    
    @property
    def performance_report(self) -> Optional[PerformanceReport]:
        """最後のパフォーマンスレポートを取得"""
        return self._last_report
    
    def find_window(self) -> bool:
        """Kindleウィンドウを検索"""
        return self._window.find_window()
    
    def run(
        self,
        num_pages: Optional[int] = None,
        output_filename: Optional[str] = None,
        progress_callback: Optional[Callable] = None,
        measure_performance: bool = True
    ) -> Optional[str]:
        """
        キャプチャからPDF生成までを実行
        
        Args:
            num_pages: ページ数（Noneで自動モード）
            output_filename: 出力ファイル名
            progress_callback: 進捗コールバック
            measure_performance: パフォーマンス計測を行うかどうか
            
        Returns:
            出力PDFのパス（失敗時はNone）
        """
        filename = output_filename or self._config.default_filename
        
        if measure_performance:
            self._perf.start_session()
        
        try:
            with self._perf.measure("ウィンドウ検索"):
                self._window.ensure_found()
            
            if num_pages is None:
                with self._perf.measure("自動キャプチャ"):
                    captured = self._capture.capture_all_pages(progress_callback)
            else:
                with self._perf.measure(f"{num_pages}ページキャプチャ"):
                    captured = self._capture.capture_pages(num_pages, progress_callback)
            
            if not captured:
                logger.error("キャプチャに失敗しました")
                return None
            
            with self._perf.measure("PDF生成"):
                pdf_path = self._pdf.generate(captured, filename)
            
            if measure_performance:
                self._perf.end_session(page_count=len(captured))
                self._last_report = self._perf.get_report()
                logger.info(f"パフォーマンス: 総時間={self._last_report.total_duration:.2f}秒, "
                           f"ページ平均={self._last_report.avg_page_time:.2f}秒")
            
            return pdf_path
            
        except WindowNotFoundError:
            logger.error("Kindleウィンドウが見つかりません")
            return None
        except Exception as e:
            logger.error(f"エラーが発生しました: {e}")
            return None
        finally:
            if not self._config.keep_temp_files:
                self._capture.cleanup()
    
    def print_performance_report(self):
        """パフォーマンスレポートを出力"""
        if self._last_report:
            self._perf.print_report()
        else:
            print("パフォーマンスデータがありません")
