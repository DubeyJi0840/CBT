import os
import pymupdf
import cv2
import numpy as np
import re
from PIL import Image
import io
from rapidocr_onnxruntime import RapidOCR

QUESTIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'questions')
ocr = RapidOCR()

sets = [
    ('set_1', 'set =1.pdf', 7),
    ('set_2', 'set -2.pdf', 7),
    ('set_3', 'set -3.pdf', 7),
    ('set_4', 'set -4.pdf', 7),
    ('set_5', 'set -5.pdf', 8),
    ('set_6', 'set-6.pdf', 8),
    ('set_7', 'set-7.pdf', 9),
    ('set_8', 'set 8.pdf', 8),
    ('set_9', 'set 9.pdf', 8),
    ('set_10', 'set 10.pdf', 8)
]

def test_extract_keys():
    for set_id, fname, page_idx in sets:
        path = os.path.join(QUESTIONS_DIR, fname)
        doc = pymupdf.open(path)
        page = doc[page_idx]
        pix = page.get_pixmap(dpi=200)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        img_np = np.array(img)
        
        # Test normal OCR + inverted OCR
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        inv = cv2.bitwise_not(gray)
        
        res1, _ = ocr(gray)
        res2, _ = ocr(inv)
        
        found = {}
        for res in [res1, res2]:
            if not res: continue
            for item in res:
                t = item[1].strip()
                # match patterns: "1. [A]" or "1 [A]" or "1-A" or "1.A" or "1 [A" or "1 (A)"
                m = re.search(r'\b(\d{1,3})[\.\s\:\-\)]*[\(\[\{\/\\]*([A-Da-d])[\)\]\}\/\\]*', t)
                if m:
                    q = int(m.group(1))
                    a = m.group(2).upper()
                    if 1 <= q <= 100:
                        if q not in found:
                            found[q] = a
                            
        print(f"{set_id} ({fname}): extracted {len(found)} keys out of 100")
        doc.close()

if __name__ == '__main__':
    test_extract_keys()

