"""
パフォーマンス測定モジュール

キャプチャ・PDF生成処理の実行時間を計測します。
"""

import time
import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class TimingResult:
    """計測結果"""
    name: str
    start_time: float
    end_time: float
    
    @property
    def duration(self) -> float:
        """実行時間（秒）"""
        return self.end_time - self.start_time
    
    @property
    def duration_ms(self) -> float:
        """実行時間（ミリ秒）"""
        return self.duration * 1000


@dataclass
class PerformanceReport:
    """パフォーマンスレポート"""
    
    timings: List[TimingResult] = field(default_factory=list)
    page_count: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def total_duration(self) -> float:
        """総実行時間（秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return sum(t.duration for t in self.timings)
    
    @property
    def avg_page_time(self) -> float:
        """ページあたりの平均時間（秒）"""
        if self.page_count == 0:
            return 0
        return self.total_duration / self.page_count
    
    def get_timing(self, name: str) -> Optional[TimingResult]:
        """名前で計測結果を取得"""
        for t in self.timings:
            if t.name == name:
                return t
        return None
    
    def summary(self) -> str:
        """サマリーを生成"""
        lines = [
            "=" * 50,
            "パフォーマンスレポート",
            "=" * 50,
            f"総ページ数: {self.page_count}",
            f"総実行時間: {self.total_duration:.2f}秒",
            f"ページ平均: {self.avg_page_time:.2f}秒/ページ",
            "",
            "詳細:",
        ]
        
        for t in self.timings:
            lines.append(f"  {t.name}: {t.duration:.3f}秒 ({t.duration_ms:.1f}ms)")
        
        lines.append("=" * 50)
        return "\n".join(lines)


class PerformanceMonitor:
    """パフォーマンス計測クラス"""
    
    def __init__(self):
        self._report = PerformanceReport()
        self._current_timer: Optional[str] = None
        self._timer_start: float = 0
    
    def start_session(self):
        """セッション開始"""
        self._report = PerformanceReport()
        self._report.start_time = datetime.now()
        logger.info("パフォーマンス計測開始")
    
    def end_session(self, page_count: int = 0):
        """セッション終了"""
        self._report.end_time = datetime.now()
        self._report.page_count = page_count
        logger.info(f"パフォーマンス計測終了: {self._report.total_duration:.2f}秒")
    
    @contextmanager
    def measure(self, name: str):
        """計測コンテキストマネージャ"""
        start = time.perf_counter()
        try:
            yield
        finally:
            end = time.perf_counter()
            result = TimingResult(name=name, start_time=start, end_time=end)
            self._report.timings.append(result)
            logger.debug(f"[{name}] {result.duration_ms:.1f}ms")
    
    def start_timer(self, name: str):
        """タイマー開始"""
        self._current_timer = name
        self._timer_start = time.perf_counter()
    
    def stop_timer(self):
        """タイマー停止"""
        if self._current_timer:
            end = time.perf_counter()
            result = TimingResult(
                name=self._current_timer,
                start_time=self._timer_start,
                end_time=end
            )
            self._report.timings.append(result)
            logger.debug(f"[{self._current_timer}] {result.duration_ms:.1f}ms")
            self._current_timer = None
    
    def get_report(self) -> PerformanceReport:
        """レポートを取得"""
        return self._report
    
    def print_report(self):
        """レポートを出力"""
        print(self._report.summary())


# グローバルインスタンス
_monitor = PerformanceMonitor()


def get_monitor() -> PerformanceMonitor:
    """グローバルモニターを取得"""
    return _monitor
