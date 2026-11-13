import os
import pymupdf
from rapidocr_onnxruntime import RapidOCR
import numpy as np
from PIL import Image
import io

QUESTIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'questions')
ocr = RapidOCR()

doc = pymupdf.open(os.path.join(QUESTIONS_DIR, 'set =1.pdf'))
# Check page 6 and page 7
for pno in [6, 7]:
    page = doc[pno]
    pix = page.get_pixmap(dpi=200)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    w, h = img.size
    print(f"Page {pno} size: {w} x {h}")
    res, _ = ocr(np.array(img))
    print(f"Total detected on page {pno}: {len(res) if res else 0}")
    # Print items with x < 150
    for box, text, conf in res:
        min_x = min(pt[0] for pt in box)
        min_y = min(pt[1] for pt in box)
        if min_x < 150:
            print(f"  Page {pno} x={min_x:.1f}, y={min_y:.1f}: '{text}'")

