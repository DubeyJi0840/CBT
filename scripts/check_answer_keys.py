import os
import pymupdf
from rapidocr_onnxruntime import RapidOCR
import numpy as np
from PIL import Image
import io
import re

QUESTIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'questions')

def check_keys():
    ocr = RapidOCR()
    sets = [
        'set =1.pdf', 'set -2.pdf', 'set -3.pdf', 'set -4.pdf', 'set -5.pdf',
        'set-6.pdf', 'set-7.pdf', 'set 8.pdf', 'set 9.pdf', 'set 10.pdf'
    ]
    
    for s in sets:
        path = os.path.join(QUESTIONS_DIR, s)
        doc = pymupdf.open(path)
        last_page_idx = len(doc) - 1
        page = doc[last_page_idx]
        pix = page.get_pixmap(dpi=150)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        res, _ = ocr(np.array(img))
        
        # Check for answer key patterns like "1. [A]" or "100. [C]"
        lines = [r[1] for r in res] if res else []
        joined = " ".join(lines)
        matches = re.findall(r'\b(\d{1,3})[\.\s\:\-\)]+[\[\(\{\/\\]*([A-Da-d])[\]\)\}\/\\]*', joined)
        
        print(f"=== {s} (Total pages: {len(doc)}) ===")
        print(f"  Last page ({last_page_idx}): {len(lines)} OCR lines, {len(matches)} answer key matches detected.")
        if len(matches) < 20 and len(doc) > 1:
            # Maybe on second-to-last page?
            p_prev = doc[last_page_idx - 1]
            pix_p = p_prev.get_pixmap(dpi=150)
            res_p, _ = ocr(np.array(Image.open(io.BytesIO(pix_p.tobytes("png")))))
            lines_p = [r[1] for r in res_p] if res_p else []
            matches_p = re.findall(r'\b(\d{1,3})[\.\s\:\-\)]+[\[\(\{\/\\]*([A-Da-d])[\]\)\}\/\\]*', " ".join(lines_p))
            print(f"  Page {last_page_idx - 1}: {len(matches_p)} answer key matches")
            
        # Sample matches
        print(f"  Sample keys: {matches[:10]} ... {matches[-5:] if len(matches) > 5 else ''}")
        doc.close()

if __name__ == '__main__':
    check_keys()

