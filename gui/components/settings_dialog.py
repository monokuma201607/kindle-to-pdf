
import logging
import customtkinter as ctk
from kindle_capture import CaptureConfig
from gui.components.crop_dialog import CropAdjustDialog

logger = logging.getLogger(__name__)

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
        CropAdjustDialog(self, self.config, self.parent.parent._service)
    
    def _save(self):
        """設定を保存"""
        try:
            self.config.delay = float(self.delay_entry.get())
            self.config.similarity_threshold = float(self.threshold_entry.get())
            self.config.max_pages = int(self.max_pages_entry.get())
            self.destroy()
        except ValueError as e:
            logger.error(f"設定値が無効です: {e}")
