
import os
import sys
import logging
from kindle_capture.toc_parser import TOCParser

# Configuration de logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_ocr():
    image_path = "temp_processed_toc.png"
    if not os.path.exists(image_path):
        print(f"Error: {image_path} not found.")
        return

    print(f"Testing OCR on {image_path}...")
    
    try:
        parser = TOCParser()
        # Ensure we point to the correct tessdata if needed
        # parser._get_tessdata_config is called internally
        
        chapters = parser.extract_from_image(image_path)
        
        print("\n--- OCR Results ---")
        if not chapters:
            print("No chapters found (empty list returned).")
        
        for ch in chapters:
            print(f"Title: {ch.title} | Page: {ch.page}")
            
    except Exception as e:
        print(f"Exception during OCR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ocr()
