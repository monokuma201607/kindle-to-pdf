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
    
    def generate(self, image_files: List[str], filename: str = "output.pdf", direction: str = "L2R") -> str:
        """
        画像ファイルからPDFを生成
        
        Args:
            image_files: 画像ファイルパスのリスト
            filename: 出力PDFファイル名
            direction: 読み方向 ("L2R" or "R2L")
            
        Returns:
            出力PDFの絶対パス
            
        Raises:
            PDFGenerationError: PDF生成に失敗した場合
        """
        if not image_files:
            raise PDFGenerationError("画像ファイルが指定されていません")
        
        output_path = self._output_dir / filename
        logger.info(f"PDF生成開始: {len(image_files)}ページ -> {output_path} (Direction: {direction})")
        
        try:
            # Step 1: Create PDF with img2pdf
            pdf_bytes = img2pdf.convert(image_files)
            
            # Step 2: Write to temp file or memory to add metadata
            import io
            from pypdf import PdfReader, PdfWriter
            
            # Create a reader from the img2pdf bytes
            reader = PdfReader(io.BytesIO(pdf_bytes))
            writer = PdfWriter()
            writer.append_pages_from_reader(reader)
            
            # Set direction
            # /Direction: /L2R or /R2L
            dir_value = "/R2L" if direction == "R2L" else "/L2R"
            
            # For pypdf >= 6.4.0, we need to create preferences first
            if hasattr(writer, 'create_viewer_preferences'):
                writer.create_viewer_preferences()
                writer.viewer_preferences.direction = dir_value
            else:
                # Fallback for older versions (though not expected with current env)
                writer.viewer_preferences = {"/Direction": dir_value}
            
            # Write final output
            with open(output_path, "wb") as f:
                writer.write(f)
            
            logger.info(f"PDF生成完了: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"PDF生成エラー: {e}")
            raise PDFGenerationError(f"PDFの生成に失敗しました: {e}")
