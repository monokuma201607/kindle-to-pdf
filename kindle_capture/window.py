"""
ウィンドウ操作モジュール

Windowsウィンドウの検出、アクティブ化、座標取得を担当します。
"""

import time
import logging
from typing import Optional, Tuple, List

import win32gui
import win32con

from kindle_capture.exceptions import WindowNotFoundError, WindowActivationError

logger = logging.getLogger(__name__)


class WindowManager:
    """Windowsウィンドウ操作を管理するクラス"""
    
    def __init__(self, keywords: List[str], activation_delay: float = 0.3):
        """
        初期化
        
        Args:
            keywords: ウィンドウ検索に使用するキーワードリスト
            activation_delay: ウィンドウアクティブ化後の待機時間（秒）
        """
        self._keywords = keywords
        self._activation_delay = activation_delay
        self._hwnd: Optional[int] = None
    
    @property
    def hwnd(self) -> Optional[int]:
        """現在のウィンドウハンドル"""
        return self._hwnd
    
    @property
    def is_found(self) -> bool:
        """ウィンドウが見つかっているかどうか"""
        return self._hwnd is not None
    
    def find_window(self, exclude_keywords: Optional[List[str]] = None) -> bool:
        """
        キーワードに一致するウィンドウを検索
        
        Args:
            exclude_keywords: 除外するキーワードリスト(デフォルトで自身やエディタを除外)
        
        Returns:
            ウィンドウが見つかった場合True
        """
        self._hwnd = None
        
        # デフォルトで除外するパターン
        default_excludes = [
            "Capture",              # 自分自身
            "capture", 
            "Visual Studio Code",   # VS Code
            "- Visual Studio",      # Visual Studio IDE
            ".py -",                # ファイル名 (エディタのタイトルパターン)
            ".md -",                # ファイル名 (エディタのタイトルパターン)
            "\\kindle\\",           # パス
            "/kindle/",             # パス
        ]
        exclude = exclude_keywords or default_excludes
        
        def enum_callback(hwnd: int, results: List[int]) -> bool:
            title = win32gui.GetWindowText(hwnd)
            
            # 空のタイトルは無視
            if not title:
                return True
            
            # 除外キーワードをチェック
            for ex_keyword in exclude:
                if ex_keyword in title:
                    return True  # スキップ
            
            # 検索キーワードをチェック
            for keyword in self._keywords:
                if keyword in title:
                    results.append(hwnd)
                    logger.debug(f"ウィンドウ発見: '{title}' (hwnd={hwnd})")
                    return True
            return True
        
        windows: List[int] = []
        win32gui.EnumWindows(enum_callback, windows)
        
        if windows:
            self._hwnd = windows[0]
            title = win32gui.GetWindowText(self._hwnd)
            logger.info(f"Kindleウィンドウを検出: '{title}' (hwnd={self._hwnd})")
            return True
        
        logger.warning("Kindleウィンドウが見つかりません")
        return False
    
    def get_rect(self) -> Optional[Tuple[int, int, int, int]]:
        """
        ウィンドウの座標を取得
        
        Returns:
            (left, top, right, bottom) のタプル、または None
        """
        if not self._hwnd:
            return None
        
        try:
            rect = win32gui.GetWindowRect(self._hwnd)
            logger.debug(f"ウィンドウ座標: {rect}")
            return rect
        except Exception as e:
            logger.error(f"ウィンドウ座標の取得に失敗: {e}")
            return None
    
    def get_size(self) -> Optional[Tuple[int, int]]:
        """
        ウィンドウサイズを取得
        
        Returns:
            (width, height) のタプル、または None
        """
        rect = self.get_rect()
        if rect:
            left, top, right, bottom = rect
            return (right - left, bottom - top)
        return None
    
    def get_title(self) -> Optional[str]:
        """
        ウィンドウタイトルを取得
        
        Returns:
            ウィンドウタイトル、または None
        """
        if not self._hwnd:
            return None
        
        try:
            return win32gui.GetWindowText(self._hwnd)
        except Exception as e:
            logger.error(f"ウィンドウタイトルの取得に失敗: {e}")
            return None
    
    def get_book_title(self) -> Optional[str]:
        """
        Kindleウィンドウタイトルから書籍名を抽出
        
        タイトル形式: "[ユーザー名]の Kindle for PC 4 - [書籍名]"
        
        Returns:
            書籍名、または None
        """
        title = self.get_title()
        if not title:
            return None
        
        # "- " の後が書籍名
        if " - " in title:
            book_title = title.split(" - ", 1)[1]
            # ファイル名として使えない文字を置換
            invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
            for char in invalid_chars:
                book_title = book_title.replace(char, '_')
            logger.debug(f"書籍名を抽出: {book_title}")
            return book_title
        
        return None
    
    def activate(self) -> None:
        """
        ウィンドウをアクティブにする
        
        Raises:
            WindowNotFoundError: ウィンドウが見つからない場合
            WindowActivationError: アクティブ化に失敗した場合
        """
        if not self._hwnd:
            raise WindowNotFoundError()
        
        try:
            win32gui.ShowWindow(self._hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(self._hwnd)
            time.sleep(self._activation_delay)
            logger.debug("ウィンドウをアクティブ化しました")
        except Exception as e:
            logger.error(f"ウィンドウのアクティブ化に失敗: {e}")
            raise WindowActivationError(f"ウィンドウのアクティブ化に失敗: {e}")
    
    def ensure_found(self) -> None:
        """
        ウィンドウが見つかっていることを確認し、なければ検索
        
        Raises:
            WindowNotFoundError: ウィンドウが見つからない場合
        """
        if not self._hwnd:
            if not self.find_window():
                raise WindowNotFoundError()
