"""
設定管理モジュール

アプリケーション設定をdataclassで管理し、YAMLファイルからの読み込みをサポートします。
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class CaptureConfig:
    """キャプチャ設定を管理するデータクラス"""
    
    # キャプチャ設定
    delay: float = 1.0
    """キャプチャ間の待機時間（秒）"""
    
    similarity_threshold: float = 0.99
    """画像比較の類似度閾値（0.0-1.0）"""
    
    max_pages: int = 9999
    """自動モードの最大ページ数"""
    
    # ウィンドウ設定
    window_keywords: List[str] = field(default_factory=lambda: ["Kindle for PC"])
    """ウィンドウ検索キーワード"""
    
    activation_delay: float = 0.3
    """ウィンドウアクティブ化後の待機時間（秒）"""
    
    # クロップ設定（UI要素を除外するためのマージン）
    margin_top: int = 75
    """上部マージン（メニューバー除外用）"""
    
    margin_bottom: int = 30
    """下部マージン（ページ番号除外用）"""
    
    margin_left: int = 150
    """左マージン（黒帯除外用）"""
    
    margin_right: int = 150
    """右マージン（黒帯除外用）"""
    
    # 出力設定
    output_dir: str = ""
    """出力ディレクトリ（空の場合はカレントディレクトリ）"""
    
    default_filename: str = "output.pdf"
    """デフォルトの出力ファイル名"""
    
    # 動作設定
    start_delay: int = 3
    """開始前の待機時間（秒）"""
    
    keep_temp_files: bool = False
    """一時ファイルを保持するかどうか"""

    
    def __post_init__(self):
        """初期化後のバリデーション"""
        if not self.output_dir:
            self.output_dir = os.getcwd()
        
        if self.delay < 0:
            raise ValueError("delayは0以上である必要があります")
        
        if not (0.0 <= self.similarity_threshold <= 1.0):
            raise ValueError("similarity_thresholdは0.0〜1.0の範囲である必要があります")
        
        if self.max_pages < 1:
            raise ValueError("max_pagesは1以上である必要があります")
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> "CaptureConfig":
        """
        YAMLファイルから設定を読み込む
        
        Args:
            yaml_path: YAMLファイルのパス
            
        Returns:
            CaptureConfig インスタンス
        """
        try:
            import yaml
        except ImportError:
            logger.warning("PyYAMLがインストールされていません。デフォルト設定を使用します。")
            return cls()
        
        path = Path(yaml_path)
        if not path.exists():
            logger.info(f"設定ファイルが見つかりません: {yaml_path}。デフォルト設定を使用します。")
            return cls()
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            
            return cls._from_dict(data)
        except Exception as e:
            logger.warning(f"設定ファイルの読み込みに失敗しました: {e}。デフォルト設定を使用します。")
            return cls()
    
    @classmethod
    def _from_dict(cls, data: dict) -> "CaptureConfig":
        """辞書から設定を構築"""
        capture = data.get("capture", {})
        output = data.get("output", {})
        window = data.get("window", {})
        
        return cls(
            delay=capture.get("delay", 1.0),
            similarity_threshold=capture.get("similarity_threshold", 0.99),
            max_pages=capture.get("max_pages", 9999),
            window_keywords=window.get("keywords", ["Kindle for PC"]),
            activation_delay=window.get("activation_delay", 0.3),
            margin_top=capture.get("margin_top", 75),
            margin_bottom=capture.get("margin_bottom", 0),
            margin_left=capture.get("margin_left", 25),
            margin_right=capture.get("margin_right", 25),
            output_dir=output.get("output_dir", ""),
            default_filename=output.get("default_filename", "output.pdf"),
            start_delay=capture.get("start_delay", 3),
            keep_temp_files=capture.get("keep_temp_files", False),
        )
    
    def to_dict(self) -> dict:
        """設定を辞書形式で出力"""
        return {
            "capture": {
                "delay": self.delay,
                "similarity_threshold": self.similarity_threshold,
                "max_pages": self.max_pages,
                "start_delay": self.start_delay,
                "keep_temp_files": self.keep_temp_files,
            },
            "output": {
                "output_dir": self.output_dir,
                "default_filename": self.default_filename,
            },
            "window": {
                "keywords": self.window_keywords,
                "activation_delay": self.activation_delay,
            },
        }
