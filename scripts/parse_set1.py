import os
import pymupdf
import re
import numpy as np
from PIL import Image
import io
from rapidocr_onnxruntime import RapidOCR

QUESTIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'questions')
ocr = RapidOCR()

def extract_set1():
    doc = pymupdf.open(os.path.join(QUESTIONS_DIR, 'set =1.pdf'))
    pages_data = []
    
    for pno in range(len(doc) - 1): # exclude answer key page
        page = doc[pno]
        pix = page.get_pixmap(dpi=150)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        w, h = img.size
        
        # Two columns: left col (0 to 0.52w), right col (0.48w to w)
        img_left = img.crop((0, 0, int(w * 0.51), h))
        img_right = img.crop((int(w * 0.49), 0, w, h))
        
        res_l, _ = ocr(np.array(img_left))
        res_r, _ = ocr(np.array(img_right))
        
        # For left col
        lines_l = []
        if res_l:
            # sort by y
            res_l.sort(key=lambda item: min(pt[1] for pt in item[0]))
            for item in res_l:
                lines_l.append(item[1].strip())
                
        # For right col
        lines_r = []
        if res_r:
            res_r.sort(key=lambda item: min(pt[1] for pt in item[0]))
            for item in res_r:
                lines_r.append(item[1].strip())
                
        pages_data.append((pno + 1, lines_l, lines_r))
        print(f"Page {pno+1}: Left lines={len(lines_l)}, Right lines={len(lines_r)}")
        
    doc.close()
    return pages_data

if __name__ == '__main__':
    extract_set1()

