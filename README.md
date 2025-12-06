# 📚 kindle-to-pdf

> Capture Kindle for PC screens and export them as a single PDF file.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## ✨ Features

- 🖥️ **Modern GUI** - Clean interface with CustomTkinter
- 📐 **Crop Adjustment** - Remove black bars with live preview
- 🔄 **Auto Page Detection** - Automatically stops at the last page
- 📖 **Book Title Detection** - Auto-fills filename from Kindle window
- ⚡ **Performance Monitoring** - Track capture speed and timing
- 🎯 **Smart Window Detection** - Finds Kindle for PC automatically

## 📸 Screenshot

*GUI screenshot here*

## 🚀 Installation

### Requirements
- Windows 10/11
- Python 3.11+
- Kindle for PC

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/kindle-to-pdf.git
cd kindle-to-pdf

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 📖 Usage

### GUI Mode (Recommended)

```bash
python run_gui.py
```

1. Open a book in **Kindle for PC**
2. Launch **kindle-to-pdf**
3. Click **📐 クロップ調整** to adjust margins
4. Click **▶ キャプチャ開始** to start
5. PDF will be saved automatically

### CLI Mode

```bash
python main.py --output book.pdf --pages 10
```

Options:
- `--output, -o`: Output PDF filename
- `--pages, -n`: Number of pages to capture
- `--all, -a`: Auto mode (capture until last page)
- `--delay, -d`: Delay between captures (seconds)
- `--config, -c`: Path to config file

## ⚙️ Configuration

Edit `config.yaml` to customize:

```yaml
capture:
  delay: 0.5              # Delay between page captures
  similarity_threshold: 0.99
  margin_top: 75          # Crop top (menu bar)
  margin_bottom: 30       # Crop bottom (page number)
  margin_left: 150        # Crop left (black bar)
  margin_right: 150       # Crop right (black bar)

window:
  keywords:
    - "Kindle for PC"
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_unit.py
```

## 📁 Project Structure

```
kindle-to-pdf/
├── gui/                    # GUI application
│   └── app.py
├── kindle_capture/         # Core library
│   ├── capture.py         # Screen capture logic
│   ├── config.py          # Configuration management
│   ├── pdf_generator.py   # PDF generation
│   ├── performance.py     # Performance monitoring
│   └── window.py          # Window detection
├── tests/                  # Test suite
├── docs/                   # Documentation
├── config.yaml            # Configuration file
├── main.py                # CLI entry point
├── run_gui.py             # GUI entry point
└── requirements.txt
```

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for the modern UI
- [img2pdf](https://gitlab.mister-muffin.de/josch/img2pdf) for PDF generation
- [PyAutoGUI](https://pyautogui.readthedocs.io/) for screen capture

---

Made with ❤️ for Kindle users
