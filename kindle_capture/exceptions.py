"""
カスタム例外クラス

アプリケーション固有のエラーを定義します。
"""


class KindleCaptureError(Exception):
    """Kindle画面キャプチャの基底例外クラス"""
    pass


class WindowNotFoundError(KindleCaptureError):
    """Kindleウィンドウが見つからない場合の例外"""
    
    def __init__(self, message: str = "Kindleウィンドウが見つかりません"):
        super().__init__(message)


class WindowActivationError(KindleCaptureError):
    """ウィンドウのアクティブ化に失敗した場合の例外"""
    
    def __init__(self, message: str = "ウィンドウをアクティブにできません"):
        super().__init__(message)


class CaptureError(KindleCaptureError):
    """画面キャプチャに失敗した場合の例外"""
    
    def __init__(self, message: str = "画面のキャプチャに失敗しました"):
        super().__init__(message)


class PDFGenerationError(KindleCaptureError):
    """PDF生成に失敗した場合の例外"""
    
    def __init__(self, message: str = "PDFの生成に失敗しました"):
        super().__init__(message)
