
import logging
import tempfile
import os
import customtkinter as ctk
from PIL import Image
from kindle_capture import CaptureConfig
from kindle_capture.capture import ScreenCapture

logger = logging.getLogger(__name__)

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
            temp_path = os.path.join(tempfile.gettempdir(), "crop_preview.png")
            
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
