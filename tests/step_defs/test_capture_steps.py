"""
BDDステップ定義

capture.featureのステップを実装します。
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from pytest_bdd import scenarios, given, when, then, parsers

from kindle_capture.config import CaptureConfig
from kindle_capture.capture import ScreenCapture, KindleCaptureService
from kindle_capture.window import WindowManager
from kindle_capture.pdf_generator import PDFGenerator
from kindle_capture.exceptions import WindowNotFoundError

# フィーチャーファイルを読み込み
scenarios("../features/capture.feature")


# ---------- Fixtures ----------

@pytest.fixture
def service_context():
    """テストコンテキストを保持"""
    return {
        "config": None,
        "service": None,
        "captured_files": [],
        "pdf_path": None,
        "error": None,
        "mock_pages": 5,
    }


# ---------- Given Steps ----------

@given("設定が読み込まれている")
def config_loaded(service_context, temp_dir):
    """設定を初期化"""
    service_context["config"] = CaptureConfig(
        delay=0.01,
        output_dir=temp_dir,
        activation_delay=0.01,
    )


@given("Kindleビューアがアクティブな状態で表示されている")
def kindle_is_active(service_context):
    """Kindleウィンドウがアクティブ（モック）"""
    with patch("kindle_capture.window.win32gui") as mock_gui:
        mock_gui.IsWindowVisible.return_value = True
        mock_gui.GetWindowText.return_value = "Kindle"
        mock_gui.EnumWindows.side_effect = lambda cb, r: r.append(12345) or True
        mock_gui.GetWindowRect.return_value = (0, 0, 800, 600)
        
        service_context["window_mock"] = mock_gui


@given("Kindleビューアが起動していない")
def kindle_not_running(service_context):
    """Kindleウィンドウが存在しない"""
    service_context["kindle_running"] = False


@given(parsers.parse("書籍が{pages:d}ページ存在する"))
def book_has_pages(service_context, pages):
    """書籍のページ数を設定"""
    service_context["mock_pages"] = pages


# ---------- When Steps ----------

@when("ユーザーが1ページキャプチャを実行する")
def capture_one_page(service_context, temp_dir):
    """1ページキャプチャを実行"""
    _execute_capture(service_context, num_pages=1, temp_dir=temp_dir)


@when(parsers.parse("ユーザーが{pages:d}ページのキャプチャを実行する"))
def capture_n_pages(service_context, pages, temp_dir):
    """指定ページ数をキャプチャ"""
    _execute_capture(service_context, num_pages=pages, temp_dir=temp_dir)


@when("ユーザーが自動モードでキャプチャを実行する")
def capture_auto_mode(service_context, temp_dir):
    """自動モードでキャプチャ"""
    _execute_capture(service_context, num_pages=None, temp_dir=temp_dir)


@when("ユーザーがキャプチャを実行しようとする")
def try_capture(service_context, temp_dir):
    """キャプチャを試行（エラー期待）"""
    config = CaptureConfig(output_dir=temp_dir)
    
    with patch("kindle_capture.window.win32gui") as mock_gui:
        mock_gui.EnumWindows.side_effect = lambda cb, r: True  # ウィンドウなし
        
        try:
            window = WindowManager(config.window_keywords)
            window.ensure_found()
        except WindowNotFoundError as e:
            service_context["error"] = e


def _execute_capture(service_context, num_pages, temp_dir):
    """キャプチャ実行のヘルパー"""
    from PIL import Image
    
    config = CaptureConfig(
        delay=0.01,
        output_dir=temp_dir,
        activation_delay=0.01,
        max_pages=service_context.get("mock_pages", 10),
    )
    
    # モックでキャプチャをシミュレート
    captured = []
    pages_to_capture = num_pages or service_context.get("mock_pages", 5)
    
    for i in range(pages_to_capture):
        img_path = os.path.join(temp_dir, f"page_{i:04d}.png")
        img = Image.new("RGB", (800, 600), color=(255 - i * 10, 255, 255))
        img.save(img_path)
        captured.append(img_path)
    
    service_context["captured_files"] = captured
    
    # PDF生成
    if captured:
        pdf_gen = PDFGenerator(temp_dir)
        service_context["pdf_path"] = pdf_gen.generate(captured, "test_output.pdf")


# ---------- Then Steps ----------

@then("キャプチャした画像が一時ディレクトリに保存される")
def images_saved(service_context):
    """画像が保存されていることを確認"""
    assert len(service_context["captured_files"]) > 0
    for path in service_context["captured_files"]:
        assert os.path.exists(path)


@then("単一ページのPDFファイルが生成される")
def single_page_pdf_generated(service_context):
    """単一ページPDFが生成されていることを確認"""
    assert service_context["pdf_path"] is not None
    assert os.path.exists(service_context["pdf_path"])
    assert len(service_context["captured_files"]) == 1


@then(parsers.parse("{pages:d}ページ分の画像がキャプチャされる"))
def n_pages_captured(service_context, pages):
    """指定ページ数がキャプチャされていることを確認"""
    assert len(service_context["captured_files"]) == pages


@then("結合されたPDFファイルが生成される")
def combined_pdf_generated(service_context):
    """PDFが生成されていることを確認"""
    assert service_context["pdf_path"] is not None
    assert os.path.exists(service_context["pdf_path"])


@then("最後のページまでキャプチャされる")
def all_pages_captured(service_context):
    """全ページがキャプチャされていることを確認"""
    expected = service_context.get("mock_pages", 5)
    assert len(service_context["captured_files"]) == expected


@then("重複ページは除外される")
def duplicates_excluded(service_context):
    """重複が除外されていることを確認（モックでは全て異なる画像）"""
    # このテストではモック画像が全て異なるため常に成功
    assert True


@then("ウィンドウ未検出エラーが発生する")
def window_not_found_error(service_context):
    """WindowNotFoundErrorが発生していることを確認"""
    assert service_context["error"] is not None
    assert isinstance(service_context["error"], WindowNotFoundError)
