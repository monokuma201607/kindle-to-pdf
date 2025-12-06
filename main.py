"""
Kindle画面キャプチャ＆PDF生成プログラム

使用方法:
    python main.py              # 対話式モード
    python main.py --all        # 1冊全体を自動キャプチャ
    python main.py -n 10        # 10ページをキャプチャ

オプション:
    -n, --pages     キャプチャするページ数
    -a, --all       1冊全体を自動キャプチャ（最後のページで自動停止）
    -o, --output    出力PDFファイル名（デフォルト: output.pdf）
    -d, --delay     キャプチャ間の待機時間（秒）
    -c, --config    設定ファイルのパス
    --keep-temp     一時ファイルを保持する
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Optional

from kindle_capture import CaptureConfig, KindleCaptureService


def setup_logging(verbose: bool = False) -> None:
    """ログ設定を初期化"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def get_page_count() -> Optional[int]:
    """
    ユーザーからページ数を入力受付
    
    Returns:
        ページ数（0で自動モード=None）
    """
    while True:
        try:
            count = input("キャプチャするページ数を入力してください（0で自動モード）: ")
            count = int(count)
            if count < 0:
                print("0以上の数値を入力してください")
                continue
            return count if count > 0 else None
        except ValueError:
            print("数値を入力してください")


def print_header() -> None:
    """ヘッダーを表示"""
    print("=" * 50)
    print("Kindle画面キャプチャ＆PDF生成プログラム v1.0.0")
    print("=" * 50)
    print()


def print_progress(current: int, total: Optional[int] = None) -> None:
    """進捗を表示"""
    if total:
        print(f"  キャプチャ中: {current}/{total}")
    else:
        print(f"  キャプチャ中: {current}ページ目")


def countdown(seconds: int) -> None:
    """カウントダウン表示"""
    print(f"{seconds}秒後にキャプチャを開始します...")
    print("Kindleウィンドウをアクティブにして、キャプチャ開始位置を表示してください")
    print()
    
    for i in range(seconds, 0, -1):
        print(f"  {i}...")
        time.sleep(1)
    print()


def main() -> int:
    """メインエントリーポイント"""
    parser = argparse.ArgumentParser(
        description="Kindle画面をキャプチャしてPDFを生成します",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-n", "--pages", type=int, help="キャプチャするページ数")
    parser.add_argument("-a", "--all", action="store_true", help="1冊全体を自動キャプチャ")
    parser.add_argument("-o", "--output", type=str, help="出力PDFファイル名")
    parser.add_argument("-d", "--delay", type=float, help="キャプチャ間の待機時間（秒）")
    parser.add_argument("-c", "--config", type=str, help="設定ファイルのパス")
    parser.add_argument("--keep-temp", action="store_true", help="一時ファイルを保持")
    parser.add_argument("--start-delay", type=int, default=3, help="開始前の待機時間（秒）")
    parser.add_argument("--max-pages", type=int, help="自動モードの最大ページ数")
    parser.add_argument("-v", "--verbose", action="store_true", help="詳細ログを表示")
    
    args = parser.parse_args()
    
    # ログ設定
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # 設定読み込み
    config_path = args.config or "config.yaml"
    if Path(config_path).exists():
        config = CaptureConfig.from_yaml(config_path)
        logger.info(f"設定ファイルを読み込みました: {config_path}")
    else:
        config = CaptureConfig()
    
    # コマンドライン引数で設定を上書き
    if args.delay is not None:
        config.delay = args.delay
    if args.max_pages is not None:
        config.max_pages = args.max_pages
    if args.keep_temp:
        config.keep_temp_files = True
    
    print_header()
    
    # サービス初期化
    service = KindleCaptureService(config)
    
    # Kindleウィンドウ検索
    print("Kindleウィンドウを検索中...")
    if not service.find_window():
        print()
        print("エラー: Kindleウィンドウが見つかりません")
        print()
        print("以下を確認してください:")
        print("  1. Kindle for PCが起動していること")
        print("  2. 書籍が開かれていること")
        print("  3. ウィンドウが最小化されていないこと")
        return 1
    
    print("Kindleウィンドウを検出しました")
    size = service.window.get_size()
    if size:
        print(f"ウィンドウサイズ: {size[0]} x {size[1]}")
    print()
    
    # モード決定
    if args.all:
        num_pages = None
        mode_str = "自動（最後のページまで）"
    elif args.pages is not None:
        num_pages = args.pages
        mode_str = f"{num_pages}ページ"
    else:
        num_pages = get_page_count()
        mode_str = "自動（最後のページまで）" if num_pages is None else f"{num_pages}ページ"
    
    output_filename = args.output or config.default_filename
    
    print()
    print("設定:")
    print(f"  モード: {mode_str}")
    print(f"  出力ファイル: {output_filename}")
    print(f"  キャプチャ間隔: {config.delay}秒")
    print()
    
    countdown(args.start_delay)
    
    # キャプチャ実行
    result = service.run(
        num_pages=num_pages,
        output_filename=output_filename,
        progress_callback=lambda c, t=None: print_progress(c, t),
    )
    
    print()
    if result:
        print("=" * 50)
        print("処理完了!")
        print(f"出力ファイル: {result}")
        print("=" * 50)
        return 0
    else:
        print("処理に失敗しました")
        return 1


if __name__ == "__main__":
    sys.exit(main())
