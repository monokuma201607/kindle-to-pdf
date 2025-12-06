"""
Kindle Capture GUI起動スクリプト

使用方法:
    python run_gui.py

CustomTkinterによるモダンなデスクトップUIを起動します。
"""

import sys
from pathlib import Path

# パッケージパスを追加
sys.path.insert(0, str(Path(__file__).parent))

from gui.app import main

if __name__ == "__main__":
    main()
