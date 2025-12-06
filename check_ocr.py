
import shutil
import os
import sys

def check_tesseract():
    # Check PATH
    path = shutil.which("tesseract")
    if path:
        print(f"FOUND_IN_PATH: {path}")
        return
    
    # Check common Windows paths
    common_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Tesseract-OCR\tesseract.exe")
    ]
    
    for p in common_paths:
        if os.path.exists(p):
            print(f"FOUND_IN_COMMON: {p}")
            return
            
    print("NOT_FOUND")

if __name__ == "__main__":
    check_tesseract()
