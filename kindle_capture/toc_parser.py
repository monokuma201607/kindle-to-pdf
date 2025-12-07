"""
目次解析モジュール

画像から目次情報を抽出し、章とページ番号の構造化データとして返します。
"""


import re
import os
import unicodedata
import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple

import pytesseract
from PIL import Image

from .exceptions import TesseractNotFoundError

logger = logging.getLogger(__name__)


@dataclass
class Chapter:
    """章情報"""
    title: str
    page: int
    level: int = 1  # 階層（今のところ1固定）
    
    def __str__(self):
        return f"{self.title} ... p.{self.page}"


class TOCParser:
    """目次ページを解析するクラス"""
    
    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        初期化
        
        Args:
            tesseract_cmd: tesseract実行ファイルのパス（省略時はPATHまたは一般的パスから検索）
        """
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        else:
            self._resolve_tesseract_cmd()
            
    def _resolve_tesseract_cmd(self):
        """Tesseractコマンドのパスを解決する"""
        # 1. 既に設定されているか確認
        try:
            pytesseract.get_tesseract_version()
            return
        except:
            pass
            
        # 2. PATHから検索
        import shutil
        path = shutil.which("tesseract")
        if path:
            pytesseract.pytesseract.tesseract_cmd = path
            return

        # 3. Windowsの一般的なパスを検索
        import os
        common_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Tesseract-OCR\tesseract.exe")
        ]
        
        for p in common_paths:
            if os.path.exists(p):
                logger.info(f"Tesseract found at: {p}")
                pytesseract.pytesseract.tesseract_cmd = p
                return

    def _is_tesseract_available(self) -> bool:
        """Tesseractが利用可能か確認"""
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def _get_tessdata_config(self) -> str:
        """ローカルのtessdataディレクトリが存在する場合はその設定を返す"""
        # プロジェクトルート（このファイルの2つ上）を検索
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        tessdata_path = os.path.join(base_dir, 'tessdata')
        
        config = r'--oem 3 --psm 6'
        
        if os.path.exists(tessdata_path) and os.path.exists(os.path.join(tessdata_path, 'jpn.traineddata')):
            logger.info(f"Local tessdata found: {tessdata_path}")
            # Windowsでのパス区切り文字やスペースの問題を避けるため、引用符なしで渡す（Pythonのsubprocess処理に任せる）
            # ただし空白を含むパスの場合は注意が必要だが、ここでは簡易的に処理
            config = f'--tessdata-dir {tessdata_path} {config}'
            
        return config

    def extract_from_image(self, image_path: str, offset: int = 0) -> List[Chapter]:
        """
        画像から章情報を抽出する
        
        Args:
            image_path: 画像ファイルパス
            offset: ページ番号の補正値
            
        Returns:
            抽出された章情報のリスト
        """
        if not self._is_tesseract_available():
            logger.error("Tesseract OCRが見つかりません。")
            raise TesseractNotFoundError()
            
        logger.info(f"目次解析開始: {image_path}")
        try:
            image = Image.open(image_path)
            
            # 前処理: グレースケール化と拡大（3倍）
            # これにより小さな文字や日本語の認識精度が大幅に向上する
            gray_image = image.convert('L')
            w, h = gray_image.size
            processed_image = gray_image.resize((w * 3, h * 3), Image.Resampling.LANCZOS)
            
            # 全言語対応のため言語指定なし、または eng+jpn を試す
            # Kindleは日本語書籍が多いと想定し jpn+eng
            # ローカルのtessdataがあればそれを使う
            config = self._get_tessdata_config()
            text = pytesseract.image_to_string(processed_image, lang='jpn+eng', config=config)
            
            # 正規化 (丸数字 ⑰ -> 17 などを変換)
            text = unicodedata.normalize('NFKC', text)
            
            logger.debug(f"OCR抽出テキスト:\n{text}")
            
            chapters = self._parse_text(text, offset)
            logger.info(f"解析完了: {len(chapters)}件の章を検出")
            return chapters
            
        except Exception as e:
            logger.error(f"目次解析エラー: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
            
    def _parse_text(self, text: str, offset: int) -> List[Chapter]:
        """テキストから章とページ番号を抽出"""
        chapters = []
        
        # パターン: "章タイトル ... 123" や "Chapter 1 ... 12" など
        # 末尾が数字で終わる行を探す
        # ノイズ除去のため、あまりに短い行や数字だけの行は除外
        
        # 行ごとに処理
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 末尾の数字を抽出する正規表現
            # 例: "第一章 始まりのとき 5" -> match
            # 例: "Prologue ... 10" -> match
            
            # パターン1: 末尾が数字 (空白区切り)
            match = re.search(r'^(.*?)\s+([0-9]+)$', line)
            
            if match:
                title_part = match.group(1).strip()
                page_part = match.group(2)
                
                # タイトルがあまりに短い、あるいは記号だけなどの場合を除去
                if len(title_part) < 2:
                    continue
                
                # リーダー（...）の除去
                title_part = re.sub(r'[.．…]+$', '', title_part).strip()
                
                try:
                    page_num = int(page_part)
                    # オフセット適用（開始ページ補正）
                    # 実際のPDFページ番号 = 本のページ番号 - オフセット
                    # ただし、計算結果が1未満になる場合は1とする（あるいは除外）
                    target_page = page_num - offset
                    if target_page < 1:
                        target_page = 1
                        
                    chapter = Chapter(title=title_part, page=target_page)
                    chapters.append(chapter)
                except ValueError:
                    continue
                    
        return chapters
