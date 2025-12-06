"""
PDF生成モジュール

キャプチャした画像からPDFファイルを生成します。
"""

import os
import logging
from pathlib import Path
from typing import List

import img2pdf

from kindle_capture.exceptions import PDFGenerationError

logger = logging.getLogger(__name__)


class PDFGenerator:
    """PDFファイル生成を担当するクラス"""
    
    def __init__(self, output_dir: str):
        """
        初期化
        
        Args:
            output_dir: 出力ディレクトリのパス
        """
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(self, image_files: List[str], filename: str = "output.pdf") -> str:
        """
        画像ファイルからPDFを生成
        
        Args:
            image_files: 画像ファイルパスのリスト
            filename: 出力PDFファイル名
            
        Returns:
            出力PDFの絶対パス
            
        Raises:
            PDFGenerationError: PDF生成に失敗した場合
        """
        if not image_files:
            raise PDFGenerationError("画像ファイルが指定されていません")
        
        output_path = self._output_dir / filename
        logger.info(f"PDF生成開始: {len(image_files)}ページ -> {output_path}")
        
        try:
            with open(output_path, "wb") as f:
                f.write(img2pdf.convert(image_files))
            
            logger.info(f"PDF生成完了: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"PDF生成エラー: {e}")
            raise PDFGenerationError(f"PDFの生成に失敗しました: {e}")
