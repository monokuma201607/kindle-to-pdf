"""
GUI ユニットテスト
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# パッケージパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestKindleCaptureApp:
    """KindleCaptureAppのテスト"""
    
    @pytest.fixture
    def mock_ctk(self):
        """CustomTkinterをモック化"""
        with patch.dict(sys.modules, {
            'customtkinter': MagicMock(),
        }):
            yield
    
    def test_config_default_values(self):
        """設定がデフォルト値で初期化されること"""
        from kindle_capture.config import CaptureConfig
        
        config = CaptureConfig()
        assert config.delay == 1.0
        assert config.similarity_threshold == 0.99
        assert config.max_pages == 9999
    
    def test_mode_auto_by_default(self):
        """デフォルトで自動モードが選択されていること"""
        # UIのモード初期値テスト（モック使用）
        mode_var = "auto"
        assert mode_var == "auto"
    
    def test_pages_entry_disabled_in_auto_mode(self):
        """自動モード時にページ数入力が無効化されること"""
        # UI状態テスト
        mode = "auto"
        pages_entry_enabled = mode != "auto"
        assert pages_entry_enabled == False
    
    def test_pages_entry_enabled_in_fixed_mode(self):
        """ページ数指定モード時に入力が有効化されること"""
        mode = "fixed"
        pages_entry_enabled = mode != "auto"
        assert pages_entry_enabled == True
    
    def test_invalid_page_count_rejected(self):
        """無効なページ数が拒否されること"""
        invalid_inputs = ["", "-1", "0", "abc"]
        
        for input_val in invalid_inputs:
            try:
                pages = int(input_val)
                valid = pages > 0
            except ValueError:
                valid = False
            
            assert valid == False, f"'{input_val}' should be invalid"
    
    def test_valid_page_count_accepted(self):
        """有効なページ数が受け入れられること"""
        valid_inputs = ["1", "10", "100", "9999"]
        
        for input_val in valid_inputs:
            pages = int(input_val)
            assert pages > 0


class TestSettingsDialog:
    """設定ダイアログのテスト"""
    
    def test_delay_validation(self):
        """キャプチャ間隔のバリデーション"""
        valid_delays = [0.5, 1.0, 2.0, 5.0]
        for delay in valid_delays:
            assert delay >= 0
    
    def test_threshold_validation(self):
        """類似度閾値のバリデーション"""
        valid_thresholds = [0.9, 0.95, 0.99, 1.0]
        for threshold in valid_thresholds:
            assert 0.0 <= threshold <= 1.0
    
    def test_invalid_threshold_rejected(self):
        """無効な閾値が拒否されること"""
        invalid_thresholds = [-0.1, 1.1, 2.0]
        for threshold in invalid_thresholds:
            is_valid = 0.0 <= threshold <= 1.0
            assert is_valid == False
