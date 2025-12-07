"""
目次確認ダイアログ

OCRで検出した目次情報をユーザーが確認・修正するためのダイアログ
"""

import customtkinter as ctk
from typing import List, Callable, Optional
from kindle_capture.toc_parser import Chapter

class TOCConfirmationDialog(ctk.CTkToplevel):
    """目次確認・修正ダイアログ"""
    
    def __init__(self, parent, chapters: List[Chapter], on_confirm: Callable[[List[Chapter]], None], on_scan_next: Optional[Callable[[], List[Chapter]]] = None):
        super().__init__(parent)
        
        self.chapters = chapters
        self.on_confirm = on_confirm
        self.on_scan_next = on_scan_next
        
        self.title("目次情報の確認")
        self.geometry("600x700")
        
        # モーダル設定
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        
    def _create_widgets(self):
        # メインフレーム
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 説明
        ctk.CTkLabel(
            main_frame, 
            text="検出された目次情報です。必要に応じて修正してください。\n"
                 "「開始」ボタンを押すと、この情報を元にPDFのしおりを作成します。",
            justify="left"
        ).pack(anchor="w", pady=(0, 20))
        
        # スクロール可能なフレーム（チャプターリスト用）
        self.scroll_frame = ctk.CTkScrollableFrame(main_frame)
        self.scroll_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        self.chapter_rows = []
        
        # ヘッダー
        header_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(header_frame, text="章タイトル", font=("", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="ページ番号", font=("", 12, "bold")).pack(side="right", padx=35)
        
        # 空の場合のメッセージ
        if not self.chapters:
            ctk.CTkLabel(self.scroll_frame, text="目次情報が検出されませんでした").pack(pady=20)
        
        # リスト表示
        for i, chapter in enumerate(self.chapters):
            self._add_row(chapter)
            
        # オフセット入力エリア
        offset_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        offset_frame.pack(fill="x", pady=(10, 0))
        
        ctk.CTkLabel(offset_frame, text="開始ページ補正:").pack(side="left")
        self.offset_entry = ctk.CTkEntry(offset_frame, width=60)
        self.offset_entry.pack(side="left", padx=5)
        self.offset_entry.insert(0, "0")
        ctk.CTkLabel(offset_frame, text="(目次のページ番号 - 補正値 = PDFページ番号)").pack(side="left", padx=5)
            
        # ボタンエリア
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(20, 0))
        
        add_btn = ctk.CTkButton(
            btn_frame,
            text="+ 章を追加",
            width=100,
            command=self._add_empty_row
        )
        add_btn.pack(side="left")
        
        scan_next_btn = ctk.CTkButton(
            btn_frame,
            text="📑 次のページも解析",
            width=140,
            fg_color="#3b82f6",
            hover_color="#2563eb",
            command=self._scan_next_page
        )
        scan_next_btn.pack(side="left", padx=10)
        
        confirm_btn = ctk.CTkButton(
            btn_frame,
            text="キャプチャ開始",
            width=150,
            fg_color="#22c55e",
            command=self._confirm
        )
        confirm_btn.pack(side="right")
        
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="キャンセル",
            width=100,
            fg_color="transparent",
            border_width=1,
            command=self.destroy
        )
        cancel_btn.pack(side="right", padx=10)

    def _scan_next_page(self):
        """次のページを解析して追加"""
        if not self.on_scan_next:
            return
            
        # UIを一時的に無効化したいが、CTkには簡単な方法がないので
        # 簡易的な待機表示を行う（プログレスバーなどが望ましいが）
        
        try:
            new_chapters = self.on_scan_next()
            if new_chapters:
                for chapter in new_chapters:
                    self._add_row(chapter)
        except Exception as e:
            print(f"Error scanning next page: {e}")

    def _add_row(self, chapter: Optional[Chapter] = None):
        """行を追加"""
        row_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        row_frame.pack(fill="x", pady=2)
        
        # 削除ボタン
        del_btn = ctk.CTkButton(
            row_frame,
            text="×",
            width=25,
            height=25,
            fg_color="#ef4444",
            command=lambda f=row_frame: self._delete_row(f)
        )
        del_btn.pack(side="left", padx=(0, 5))
        
        # タイトル入力
        title_entry = ctk.CTkEntry(row_frame, width=350)
        title_entry.pack(side="left", fill="x", expand=True, padx=5)
        if chapter:
            title_entry.insert(0, chapter.title)
            
        # ページ入力
        page_entry = ctk.CTkEntry(row_frame, width=60)
        page_entry.pack(side="right", padx=5)
        if chapter:
            page_entry.insert(0, str(chapter.page))
            
        self.chapter_rows.append({
            "frame": row_frame,
            "title": title_entry,
            "page": page_entry
        })
        
    def _add_empty_row(self):
        """空の行を追加"""
        self._add_row(Chapter("", 1))
        
    def _delete_row(self, frame):
        """行を削除"""
        frame.destroy()
        # リストから除去
        self.chapter_rows = [row for row in self.chapter_rows if row["frame"] != frame]
        
    def _confirm(self):
        """確定処理"""
        result_chapters = []
        try:
            offset = int(self.offset_entry.get())
            
            for row in self.chapter_rows:
                title = row["title"].get().strip()
                page_str = row["page"].get().strip()
                
                if not title:
                    continue
                    
                original_page = int(page_str)
                # オフセット適用
                final_page = original_page - offset
                if final_page < 1:
                    final_page = 1
                    
                chapter = Chapter(title=title, page=final_page)
                result_chapters.append(chapter)
                
            # ページ順にソート
            result_chapters.sort(key=lambda x: x.page)
            
            self.on_confirm(result_chapters)
            self.destroy()
            
        except ValueError:
            # エラー表示できないのでログだけ（簡易）
            print("無効な数値があります")
