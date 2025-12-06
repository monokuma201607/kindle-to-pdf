"""
Kindle Capture デスクトップアプリケーション

CustomTkinterを使用したモダンなGUIを提供します。
"""

import os
import sys
import threading
import logging
from pathlib import Path
from typing import Optional
from tkinter import filedialog

import customtkinter as ctk
from PIL import Image

# パッケージパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from kindle_capture import CaptureConfig, KindleCaptureService
from kindle_capture.exceptions import WindowNotFoundError

logger = logging.getLogger(__name__)


class KindleCaptureApp(ctk.CTk):
    """Kindle Capture メインアプリケーション"""
    
    # ウィンドウ設定
    WINDOW_WIDTH = 520
    WINDOW_HEIGHT = 800
    
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
        
        # 設定ボタン
        self._create_settings_button()
    
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
    
    def _start_capture(self):
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
        self.stop_btn.configure(state="normal")
        self.progress_bar.set(0)
        self.progress_label.configure(text="開始準備中...")
        
        # カウントダウン開始
        self._countdown(3, num_pages, output_file)
    
    def _countdown(self, seconds: int, num_pages: Optional[int], output_file: str):
        """カウントダウン表示"""
        if seconds > 0:
            self.progress_label.configure(text=f"開始まで {seconds} 秒...")
            self.after(1000, lambda: self._countdown(seconds - 1, num_pages, output_file))
        else:
            # キャプチャスレッド開始
            self._capture_thread = threading.Thread(
                target=self._capture_worker,
                args=(num_pages, output_file),
                daemon=True
            )
            self._capture_thread.start()
    
    def _capture_worker(self, num_pages: Optional[int], output_file: str):
        """キャプチャワーカースレッド"""
        try:
            def progress_callback(current, total=None):
                self._captured_count = current
                self.after(0, lambda: self._update_progress(current, total))
                return not self._stop_requested
            
            result = self._service.run(
                num_pages=num_pages,
                output_filename=output_file,
                progress_callback=progress_callback
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


class SettingsDialog(ctk.CTkToplevel):
    """設定ダイアログ"""
    
    def __init__(self, parent, config: CaptureConfig):
        super().__init__(parent)
        
        self.config = config
        self.parent = parent
        
        self.title("⚙️ 設定")
        self.geometry("400x400")
        self.resizable(False, False)
        
        # モーダル化
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
    
    def _create_widgets(self):
        """ウィジェットを作成"""
        main_frame = ctk.CTkFrame(self, corner_radius=0)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # キャプチャ間隔
        delay_label = ctk.CTkLabel(main_frame, text="キャプチャ間隔（秒）")
        delay_label.pack(anchor="w", pady=(0, 5))
        
        self.delay_entry = ctk.CTkEntry(main_frame, width=100)
        self.delay_entry.pack(anchor="w")
        self.delay_entry.insert(0, str(self.config.delay))
        
        # 類似度閾値
        threshold_label = ctk.CTkLabel(main_frame, text="重複検出閾値（0.0-1.0）")
        threshold_label.pack(anchor="w", pady=(15, 5))
        
        self.threshold_entry = ctk.CTkEntry(main_frame, width=100)
        self.threshold_entry.pack(anchor="w")
        self.threshold_entry.insert(0, str(self.config.similarity_threshold))
        
        # 最大ページ数
        max_pages_label = ctk.CTkLabel(main_frame, text="最大ページ数（自動モード）")
        max_pages_label.pack(anchor="w", pady=(15, 5))
        
        self.max_pages_entry = ctk.CTkEntry(main_frame, width=100)
        self.max_pages_entry.pack(anchor="w")
        self.max_pages_entry.insert(0, str(self.config.max_pages))
        
        # クロップ調整ボタン
        crop_btn = ctk.CTkButton(
            main_frame,
            text="📐 クロップ調整（プレビュー）",
            command=self._open_crop_dialog
        )
        crop_btn.pack(anchor="w", pady=(20, 0))
        
        # ボタン
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(30, 0))
        
        save_btn = ctk.CTkButton(
            btn_frame,
            text="保存",
            command=self._save
        )
        save_btn.pack(side="right")
        
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="キャンセル",
            fg_color="transparent",
            border_width=1,
            command=self.destroy
        )
        cancel_btn.pack(side="right", padx=(0, 10))
    
    def _open_crop_dialog(self):
        """クロップ調整ダイアログを開く"""
        CropAdjustDialog(self, self.config, self.parent._service)
    
    def _save(self):
        """設定を保存"""
        try:
            self.config.delay = float(self.delay_entry.get())
            self.config.similarity_threshold = float(self.threshold_entry.get())
            self.config.max_pages = int(self.max_pages_entry.get())
            self.destroy()
        except ValueError as e:
            logger.error(f"設定値が無効です: {e}")


class CropAdjustDialog(ctk.CTkToplevel):
    """クロップ調整ダイアログ（プレビュー付き）"""
    
    def __init__(self, parent, config: CaptureConfig, service):
        super().__init__(parent)
        
        self.config = config
        self.service = service
        
        self.title("📐 クロップ調整")
        self.geometry("700x700")
        self.resizable(False, False)
        
        self.transient(parent)
        self.grab_set()
        
        # 一時的なマージン値
        self.temp_top = config.margin_top
        self.temp_bottom = config.margin_bottom
        self.temp_left = config.margin_left
        self.temp_right = config.margin_right
        
        self._create_widgets()
        self._update_preview()
    
    def _create_widgets(self):
        """ウィジェットを作成"""
        main_frame = ctk.CTkFrame(self, corner_radius=0)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # プレビューエリア
        preview_label = ctk.CTkLabel(main_frame, text="プレビュー（クロップ後の画像）", font=ctk.CTkFont(size=14, weight="bold"))
        preview_label.pack(anchor="w", pady=(0, 10))
        
        self.preview_frame = ctk.CTkFrame(main_frame, fg_color="#1a1a1a", corner_radius=8)
        self.preview_frame.pack(fill="x", pady=(0, 15))
        
        self.preview_label = ctk.CTkLabel(
            self.preview_frame,
            text="プレビューを読み込み中...",
            width=650,
            height=300
        )
        self.preview_label.pack(padx=10, pady=10)
        
        # スライダーエリア
        slider_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        slider_frame.pack(fill="x", pady=10)
        
        # 上マージン
        self._create_slider(slider_frame, "上（メニュー除外）", "top", 0, 150, self.temp_top)
        
        # 下マージン
        self._create_slider(slider_frame, "下（ページ番号除外）", "bottom", 0, 100, self.temp_bottom)
        
        # 左マージン
        self._create_slider(slider_frame, "左（黒帯除外）", "left", 0, 200, self.temp_left)
        
        # 右マージン
        self._create_slider(slider_frame, "右（黒帯除外）", "right", 0, 200, self.temp_right)
        
        # ボタン
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(20, 0))
        
        apply_btn = ctk.CTkButton(
            btn_frame,
            text="✓ 適用",
            fg_color="#22c55e",
            command=self._apply
        )
        apply_btn.pack(side="right")
        
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="キャンセル",
            fg_color="transparent",
            border_width=1,
            command=self.destroy
        )
        cancel_btn.pack(side="right", padx=(0, 10))
        
        refresh_btn = ctk.CTkButton(
            btn_frame,
            text="🔄 プレビュー更新",
            command=self._update_preview
        )
        refresh_btn.pack(side="left")
    
    def _create_slider(self, parent, label_text: str, name: str, from_: int, to: int, initial: int):
        """スライダーを作成"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=5)
        
        label = ctk.CTkLabel(frame, text=f"{label_text}:", width=150, anchor="w")
        label.pack(side="left")
        
        value_label = ctk.CTkLabel(frame, text=f"{initial}px", width=50)
        value_label.pack(side="right")
        
        slider = ctk.CTkSlider(
            frame,
            from_=from_,
            to=to,
            number_of_steps=to - from_,
            width=350,
            command=lambda v, n=name, vl=value_label: self._on_slider_change(n, v, vl)
        )
        slider.set(initial)
        slider.pack(side="left", padx=10)
        
        # マウスリリース時にプレビュー更新
        slider.bind("<ButtonRelease-1>", lambda e: self._update_preview())
        
        setattr(self, f"slider_{name}", slider)
    
    def _on_slider_change(self, name: str, value: float, value_label):
        """スライダー変更時"""
        int_value = int(value)
        value_label.configure(text=f"{int_value}px")
        setattr(self, f"temp_{name}", int_value)
    
    def _update_preview(self):
        """プレビューを更新"""
        try:
            if not self.service or not self.service.window.is_found:
                self.preview_label.configure(text="Kindleウィンドウが見つかりません")
                return
            
            # 現在のマージン設定を一時的に変更
            original_margins = (
                self.config.margin_top,
                self.config.margin_bottom,
                self.config.margin_left,
                self.config.margin_right
            )
            
            self.config.margin_top = self.temp_top
            self.config.margin_bottom = self.temp_bottom
            self.config.margin_left = self.temp_left
            self.config.margin_right = self.temp_right
            
            # スクリーンショットを取得
            import tempfile
            import os
            
            temp_path = os.path.join(tempfile.gettempdir(), "crop_preview.png")
            
            from kindle_capture.capture import ScreenCapture
            capture = ScreenCapture(self.service.window, self.config)
            
            if capture.capture_window(temp_path):
                # 画像をリサイズして表示
                img = Image.open(temp_path)
                
                # アスペクト比を維持してリサイズ
                max_width, max_height = 630, 280
                ratio = min(max_width / img.width, max_height / img.height)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                img_resized = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # CTkImageに変換
                ctk_img = ctk.CTkImage(light_image=img_resized, dark_image=img_resized, size=new_size)
                self.preview_label.configure(image=ctk_img, text="")
                self.preview_label.image = ctk_img
                
                # サイズ情報を表示
                self.preview_label.configure(text="")
            else:
                self.preview_label.configure(text="キャプチャに失敗しました")
            
            # マージンを元に戻す
            self.config.margin_top = original_margins[0]
            self.config.margin_bottom = original_margins[1]
            self.config.margin_left = original_margins[2]
            self.config.margin_right = original_margins[3]
            
        except Exception as e:
            self.preview_label.configure(text=f"エラー: {e}")
            logger.error(f"プレビュー更新エラー: {e}")
    
    def _apply(self):
        """設定を適用"""
        self.config.margin_top = self.temp_top
        self.config.margin_bottom = self.temp_bottom
        self.config.margin_left = self.temp_left
        self.config.margin_right = self.temp_right
        
        logger.info(f"クロップ設定を適用: top={self.temp_top}, bottom={self.temp_bottom}, left={self.temp_left}, right={self.temp_right}")
        self.destroy()


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
