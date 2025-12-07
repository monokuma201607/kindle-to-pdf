
import sys
import os
import shutil
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from kindle_capture.toc_parser import TOCParser
from kindle_capture.exceptions import TesseractNotFoundError
import pytesseract

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_fix():
    print("--- Verifying TOC Parser Fix ---")
    
    # 1. Reset pytesseract cmd to default to simulate fresh start
    pytesseract.pytesseract.tesseract_cmd = 'tesseract'
    
    parser = TOCParser()
    
    current_cmd = pytesseract.pytesseract.tesseract_cmd
    print(f"Resolved Tesseract Command: {current_cmd}")
    
    # Check if it looks like an absolute path (meaning our fix worked) or just 'tesseract' (meaning it relied on PATH)
    is_absolute = os.path.isabs(current_cmd)
    in_path = shutil.which("tesseract") is not None
    
    if is_absolute:
        print("SUCCESS: Tesseract path resolved to an absolute path.")
        if os.path.exists(current_cmd):
             print(f"Verified executable exists at: {current_cmd}")
        else:
             print("WARNING: Resolved path does not exist!")
    elif in_path:
        print("SUCCESS: Tesseract found in PATH.")
    else:
        print("INFO: Tesseract not found in PATH and not resolved to absolute path.")
        
    # 2. Test Exception
    # If we didn't find it, extract_from_image should raise TesseractNotFoundError
    # If we DID find it, we can't easily test the exception without mocking, but we can verify it doesn't raise it immediately.
    
    print("\n--- Testing extract_from_image behavior ---")
    
    # Create a dummy image to pass initial checks if possible, or expect error earlier
    # extract_from_image checks availability first.
    
    try:
        # We don't provide a valid image path, but we check if it raises TesseractNotFoundError first
        # parsing happens after image open. 
        # checking _is_tesseract_available happens first.
        
        # If available, it will try to open image and fail with FileNotFoundError (or OSError)
        # If NOT available, it will raise TesseractNotFoundError
        
        parser.extract_from_image("dummy_non_existent.png")
        print("Result: Function proceeded (Tesseract found). Failed later on file I/O (Expected if Tesseract is found).")
    except TesseractNotFoundError:
        print("Result: TesseractNotFoundError raised. (Expected if Tesseract is NOT found)")
        if is_absolute or in_path:
             print("FAILURE: Tesseract was resolved but Exception was raised!")
        else:
             print("SUCCESS: Correctly raised exception when missing.")
    except Exception as e:
        print(f"Result: Other exception raised: {e}")
        if "No such file" in str(e) or "cannot identify" in str(e):
             print("SUCCESS: Tesseract found, proceeded to image processing.")
        else:
             print("WARNING: Unexpected exception.")

if __name__ == "__main__":
    verify_fix()
