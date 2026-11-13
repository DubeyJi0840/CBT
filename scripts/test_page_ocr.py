import os
import pymupdf
from rapidocr_onnxruntime import RapidOCR
import numpy as np
from PIL import Image
import io

QUESTIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'questions')

def test_ocr():
    ocr = RapidOCR()
    filepath = os.path.join(QUESTIONS_DIR, 'set =1.pdf')
    doc = pymupdf.open(filepath)
    print(f"Set 1 pages: {len(doc)}")
    
    # Check page 0
    page0 = doc[0]
    pix = page0.get_pixmap(dpi=150)
    img_data = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_data))
    img_np = np.array(img)
    
    result0, elapse = ocr(img_np)
    print(f"Page 0 OCR lines: {len(result0) if result0 else 0}")
    if result0:
        for item in result0[:35]:
            print(f"  [{item[2]}] {item[1]}")
            
    # Check last page (page 7)
    page_last = doc[-1]
    pix_last = page_last.get_pixmap(dpi=150)
    img_last = Image.open(io.BytesIO(pix_last.tobytes("png")))
    result_last, elapse_last = ocr(np.array(img_last))
    print(f"\nLast page (Page {len(doc)-1}) OCR lines: {len(result_last) if result_last else 0}")
    if result_last:
        for item in result_last:
            print(f"  [{item[2]}] {item[1]}")

if __name__ == '__main__':
    test_ocr()
