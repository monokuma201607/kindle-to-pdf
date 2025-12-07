"""
Kindle Capture デスクトップアプリケーション

CustomTkinterを使用したモダンなGUIを提供します。
"""

import os
import sys
import threading
import logging
from pathlib import Path
from typing import Optional, List
from tkinter import filedialog

import customtkinter as ctk
from PIL import Image

# パッケージパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from kindle_capture import CaptureConfig, KindleCaptureService
from kindle_capture.exceptions import WindowNotFoundError, TesseractNotFoundError
from gui.components.settings_dialog import SettingsDialog
from gui.components.crop_dialog import CropAdjustDialog
from gui.toc_dialog import TOCConfirmationDialog
from kindle_capture.toc_parser import Chapter

logger = logging.getLogger(__name__)


class KindleCaptureApp(ctk.CTk):
    """Kindle Capture メインアプリケーション"""
    
    # ウィンドウ設定
    WINDOW_WIDTH = 520
    WINDOW_HEIGHT = 850
    
    def __init__(self):
        super().__init__()
        
        # テーマ設定
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # ウィンドウ設定
        self.title("🔖 Kindle Capture")
        self.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}")
        self.resizable(False, False)
        
        # 状態管理
        self._config = CaptureConfig()
        self._service: Optional[KindleCaptureService] = None
        self._capture_thread: Optional[threading.Thread] = None
        self._is_capturing = False
        self._stop_requested = False
        self._captured_count = 0
        self._total_pages: Optional[int] = None
        
        # UI構築
        self._create_widgets()
        
        # 初期状態確認
        self.after(500, self._check_kindle_window)
    
    def _create_widgets(self):
        """UIウィジェットを作成"""
        # メインフレーム
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # コントロールボタン（最上部に配置）
        self._create_control_buttons()
        
        # ヘッダー
        self._create_header()
        
        # ステータス表示
        self._create_status_section()
        
        # クロップ調整ボタン（ステータスの直後に配置）
        self._create_crop_button()
        
        # プレビューエリア
        self._create_preview_section()
        
        # モード選択
        self._create_mode_section()
        
        # ファイル選択
        self._create_file_section()
        
        # 進捗表示
        self._create_progress_section()
        
        # 設定ボタンはヘッダーに移動
        # self._create_settings_button()
    
    def _create_header(self):
        """ヘッダーを作成"""
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="🔖 Kindle Capture",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(side="left")
        
        version_label = ctk.CTkLabel(
            header_frame,
            text="v1.0.0",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        version_label.pack(side="left", padx=10)
        
        # 設定ボタンをヘッダー右側に移動
        settings_btn = ctk.CTkButton(
            header_frame,
            text="⚙️",
            width=40,
            height=30,
            fg_color="transparent",
            border_width=1,
            command=self._open_settings
        )
        settings_btn.pack(side="right", padx=10)
    
    def _create_status_section(self):
        """ステータスセクションを作成"""
        status_frame = ctk.CTkFrame(self.main_frame)
        status_frame.pack(fill="x", pady=10)
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="📚 Kindleウィンドウ: 検索中...",
            font=ctk.CTkFont(size=14)
        )
        self.status_label.pack(pady=10)
        
        self.refresh_btn = ctk.CTkButton(
            status_frame,
            text="🔄 再検出",
            width=100,
            command=self._check_kindle_window
        )
        self.refresh_btn.pack(pady=(0, 10))
    
    def _create_preview_section(self):
        """プレビューセクションを作成"""
        preview_frame = ctk.CTkFrame(self.main_frame)
        preview_frame.pack(fill="x", pady=10)
        
        preview_label = ctk.CTkLabel(
            preview_frame,
            text="プレビュー",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        preview_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        self.preview_canvas = ctk.CTkLabel(
            preview_frame,
            text="キャプチャ開始後に表示されます",
            width=460,
            height=100,
            fg_color=("#2b2b2b", "#1a1a1a"),
            corner_radius=8
        )
        self.preview_canvas.pack(padx=10, pady=(0, 10))
    
    def _create_mode_section(self):
        """モード選択セクションを作成"""
        mode_frame = ctk.CTkFrame(self.main_frame)
        mode_frame.pack(fill="x", pady=10)
        
        mode_label = ctk.CTkLabel(
            mode_frame,
            text="キャプチャモード",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        mode_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        self.mode_var = ctk.StringVar(value="auto")
        
        radio_frame = ctk.CTkFrame(mode_frame, fg_color="transparent")
        radio_frame.pack(fill="x", padx=10, pady=5)
        
        self.auto_radio = ctk.CTkRadioButton(
            radio_frame,
            text="自動（最後のページまで）",
            variable=self.mode_var,
            value="auto",
            command=self._on_mode_change
        )
        self.auto_radio.pack(side="left", padx=(0, 20))
        
        self.fixed_radio = ctk.CTkRadioButton(
            radio_frame,
            text="ページ数指定",
            variable=self.mode_var,
            value="fixed",
            command=self._on_mode_change
        )
        self.fixed_radio.pack(side="left")
        
        self.pages_entry = ctk.CTkEntry(
            radio_frame,
            width=60,
            placeholder_text="10"
        )
        self.pages_entry.pack(side="left", padx=10)
        self.pages_entry.insert(0, "10")
        self.pages_entry.configure(state="disabled")
    
    def _create_file_section(self):
        """ファイル選択セクションを作成"""
        file_frame = ctk.CTkFrame(self.main_frame)
        file_frame.pack(fill="x", pady=10)
        
        file_label = ctk.CTkLabel(
            file_frame,
            text="出力ファイル",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        file_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        entry_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
        entry_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.file_entry = ctk.CTkEntry(
            entry_frame,
            width=350,
            placeholder_text="output.pdf"
        )
        self.file_entry.pack(side="left")
        self.file_entry.insert(0, "output.pdf")
        
        browse_btn = ctk.CTkButton(
            entry_frame,
            text="📁 参照",
            width=80,
            command=self._browse_file
        )
        browse_btn.pack(side="left", padx=(10, 0))
    
    def _create_progress_section(self):
        """進捗セクションを作成"""
        progress_frame = ctk.CTkFrame(self.main_frame)
        progress_frame.pack(fill="x", pady=10)
        
        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="待機中",
            font=ctk.CTkFont(size=12)
        )
        self.progress_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame, width=440)
        self.progress_bar.pack(padx=10, pady=(0, 10))
        self.progress_bar.set(0)
    
    def _create_control_buttons(self):
        """コントロールボタンを作成"""
        # 目立つフレーム
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="#1e3a5f", corner_radius=10)
        btn_frame.pack(fill="x", pady=15, padx=5)
        
        inner_frame = ctk.CTkFrame(btn_frame, fg_color="transparent")
        inner_frame.pack(pady=15)
        
        self.start_btn = ctk.CTkButton(
            inner_frame,
            text="▶️ キャプチャ開始",
            width=220,
            height=50,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#22c55e",
            hover_color="#16a34a",
            command=self._start_capture
        )
        self.start_btn.pack(side="left", padx=10)
        
        self.toc_btn = ctk.CTkButton(
            inner_frame,
            text="📖 目次から開始",
            width=160,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#8b5cf6",
            hover_color="#7c3aed",
            command=self._start_capture_from_toc
        )
        self.toc_btn.pack(side="left", padx=10)
        
        self.stop_btn = ctk.CTkButton(
            inner_frame,
            text="⏹️ 停止",
            width=220,
            height=50,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#ef4444",
            hover_color="#dc2626",
            state="disabled",
            command=self._stop_capture
        )
        self.stop_btn.pack(side="left", padx=10)
    
    def _create_crop_button(self):
        """クロップ調整ボタンを作成（ステータス直後に配置）"""
        crop_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        crop_frame.pack(pady=5)
        
        # クロップ調整ボタン（大きく目立つ）
        self.crop_btn = ctk.CTkButton(
            crop_frame,
            text="📐 クロップ調整（黒帯除去）",
            width=250,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#3b82f6",
            hover_color="#2563eb",
            command=self._open_crop_dialog
        )
        self.crop_btn.pack()
    
    def _create_settings_button(self):
        """設定ボタンを作成"""
        settings_btn = ctk.CTkButton(
            self.main_frame,
            text="⚙️ 設定",
            width=100,
            fg_color="transparent",
            border_width=1,
            command=self._open_settings
        )
        settings_btn.pack(pady=10)
    
    def _open_crop_dialog(self):
        """クロップ調整ダイアログを直接開く"""
        if self._service and self._service.window.is_found:
            CropAdjustDialog(self, self._config, self._service)
        else:
            # Kindleが見つからない場合はエラーメッセージ
            self.progress_label.configure(
                text="⚠️ 先に「再検出」でKindleウィンドウを検出してください"
            )
    
    def _on_mode_change(self):
        """モード変更時の処理"""
        if self.mode_var.get() == "fixed":
            self.pages_entry.configure(state="normal")
        else:
            self.pages_entry.configure(state="disabled")
    
    def _browse_file(self):
        """ファイル選択ダイアログを表示"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=self.file_entry.get()
        )
        if filename:
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, filename)
    
    def _check_kindle_window(self):
        """Kindleウィンドウを検索"""
        self._service = KindleCaptureService(self._config)
        
        if self._service.find_window():
            size = self._service.window.get_size()
            size_str = f" ({size[0]}x{size[1]})" if size else ""
            self.status_label.configure(
                text=f"📚 Kindleウィンドウ: 検出済み ✓{size_str}",
                text_color="#22c55e"
            )
            self.start_btn.configure(state="normal")
            
            # 書籍名を自動取得してファイル名に設定
            book_title = self._service.window.get_book_title()
            if book_title:
                # 現在のファイル名がデフォルトまたは空の場合のみ更新
                current_filename = self.file_entry.get()
                if current_filename in ["output.pdf", "", "C:/Users/takes/Documents/output.pdf"]:
                    self.file_entry.delete(0, "end")
                    self.file_entry.insert(0, f"{book_title}.pdf")
        else:
            self.status_label.configure(
                text="📚 Kindleウィンドウ: 未検出 ✗",
                text_color="#ef4444"
            )
            self.start_btn.configure(state="disabled")
    
    def _start_capture_from_toc(self):
        """目次解析からキャプチャを開始"""
        if not self._service or not self._service.window.is_found:
            self.progress_label.configure(text="⚠️ 先に「再検出」でKindleウィンドウを検出してください")
            return
            
        self.progress_label.configure(text="目次を解析中...")
        self.toc_btn.configure(state="disabled")
        self.start_btn.configure(state="disabled")
        
        try:
            # スレッドで実行するとGUIがフリーズしないが、今回は簡易的にメインスレッドで実行
            # (Tesseractの処理時間は短いため)
            chapters = self._service.detect_toc_page()
            self.progress_label.configure(text="目次解析完了")
        except TesseractNotFoundError:
            self.progress_label.configure(text="エラー: Tesseractが見つかりません")
            self._show_error("Tesseract OCRが見つかりません。\n以下のURLからインストールしてください:\nhttps://github.com/UB-Mannheim/tesseract/wiki")
            chapters = []
        except Exception as e:
            self.progress_label.configure(text="エラー: 目次解析に失敗しました")
            self._show_error(f"目次解析エラー: {e}")
            chapters = []
        
        self.toc_btn.configure(state="normal")
        self.start_btn.configure(state="normal")
        
        # 確認ダイアログを表示
        TOCConfirmationDialog(
            self, 
            chapters, 
            on_confirm=lambda ch: self._start_capture(bookmarks=ch),
            on_scan_next=self._scan_next_toc_page
        )

    def _scan_next_toc_page(self) -> List[Chapter]:
        """次のページへ遷移して目次解析"""
        if not self._service:
            return []
            
        try:
            # 次のページへ
            self._service.turn_next_page()
            import time
            time.sleep(self._config.delay + 0.5) # ページ遷移待ち
            
            # 解析
            return self._service.detect_toc_page()
        except Exception as e:
            logger.error(f"目次追加解析エラー: {e}")
            return []
            
    def _start_capture(self, bookmarks: Optional[List[Chapter]] = None):
        """キャプチャを開始"""
        if self._is_capturing:
            return
        
        # 設定取得
        mode = self.mode_var.get()
        output_file = self.file_entry.get() or "output.pdf"
        
        num_pages = None
        if mode == "fixed":
            try:
                num_pages = int(self.pages_entry.get())
                if num_pages <= 0:
                    raise ValueError()
            except ValueError:
                self._show_error("ページ数に正の整数を入力してください")
                return
        
        self._total_pages = num_pages
        
        # UI更新
        self._is_capturing = True
        self._stop_requested = False
        self._captured_count = 0
        self.start_btn.configure(state="disabled")
        self.toc_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.stop_btn.configure(state="normal")
        self.progress_bar.set(0)
        self.progress_label.configure(text="開始準備中...")
        
        # カウントダウン開始
        self._countdown(3, num_pages, output_file, bookmarks)
    
    def _countdown(self, seconds: int, num_pages: Optional[int], output_file: str, bookmarks: Optional[List[Chapter]] = None):
        """カウントダウン表示"""
        if seconds > 0:
            self.progress_label.configure(text=f"開始まで {seconds} 秒...")
            self.after(1000, lambda: self._countdown(seconds - 1, num_pages, output_file, bookmarks))
        else:
            # キャプチャスレッド開始
            self._capture_thread = threading.Thread(
                target=self._capture_worker,
                args=(num_pages, output_file, bookmarks),
                daemon=True
            )
            self._capture_thread.start()
    
    def _capture_worker(self, num_pages: Optional[int], output_file: str, bookmarks: Optional[List[Chapter]] = None):
        """キャプチャワーカースレッド"""
        try:
            def progress_callback(current, total=None):
                self._captured_count = current
                self.after(0, lambda: self._update_progress(current, total))
                return not self._stop_requested
            
            result = self._service.run(
                num_pages=num_pages,
                output_filename=output_file,
                progress_callback=progress_callback,
                bookmarks=bookmarks
            )
            
            self.after(0, lambda: self._capture_complete(result))
            
        except Exception as e:
            self.after(0, lambda: self._capture_error(str(e)))
    
    def _update_progress(self, current: int, total: Optional[int]):
        """進捗を更新"""
        if total:
            progress = current / total
            self.progress_bar.set(progress)
            self.progress_label.configure(text=f"キャプチャ中: {current}/{total} ページ")
        else:
            # 自動モード
            self.progress_bar.set(0.5)  # 不定進捗
            self.progress_label.configure(text=f"キャプチャ中: {current} ページ目")
    
    def _capture_complete(self, result: Optional[str]):
        """キャプチャ完了"""
        self._is_capturing = False
        self.start_btn.configure(state="normal")
        self.toc_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        
        if result:
            self.progress_bar.set(1)
            
            # パフォーマンス情報を取得
            report = self._service.performance_report
            if report:
                perf_info = f" ({report.total_duration:.1f}秒, {report.avg_page_time:.2f}秒/ページ)"
            else:
                perf_info = ""
            
            self.progress_label.configure(
                text=f"✓ 完了: {self._captured_count}ページ → {Path(result).name}{perf_info}"
            )
            self._show_success(f"PDFを生成しました:\n{result}")
        else:
            self.progress_label.configure(text="キャプチャが中断されました")
    
    def _capture_error(self, error_msg: str):
        """キャプチャエラー"""
        self._is_capturing = False
        self.start_btn.configure(state="normal")
        self.toc_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.progress_label.configure(text=f"エラー: {error_msg}")
        self._show_error(error_msg)
    
    def _stop_capture(self):
        """キャプチャを停止"""
        self._stop_requested = True
        self.progress_label.configure(text="停止中...")
    
    def _open_settings(self):
        """設定ダイアログを開く"""
        SettingsDialog(self, self._config)
    
    def _show_error(self, message: str):
        """エラーダイアログを表示"""
        dialog = ctk.CTkInputDialog(text=message, title="エラー")
        # 注: CTkMessageBoxがないため簡易実装
        logger.error(message)
    
    def _show_success(self, message: str):
        """成功メッセージを表示"""
        logger.info(message)





def main():
    """アプリケーションを起動"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    
    app = KindleCaptureApp()
    app.mainloop()


if __name__ == "__main__":
    main()
