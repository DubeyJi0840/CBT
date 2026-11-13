import os
import pymupdf
from rapidocr_onnxruntime import RapidOCR
import numpy as np
from PIL import Image
import io

QUESTIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'questions')
ocr = RapidOCR()

doc = pymupdf.open(os.path.join(QUESTIONS_DIR, 'set =1.pdf'))
page = doc[7]
pix = page.get_pixmap(dpi=200)
img = Image.open(io.BytesIO(pix.tobytes("png")))
res, _ = ocr(np.array(img))

items = []
for box, text, conf in res:
    min_x = min(pt[0] for pt in box)
    min_y = min(pt[1] for pt in box)
    items.append((min_y, min_x, text, conf))

items.sort(key=lambda it: it[0]) # sort by Y

print(f"All {len(items)} items on Page 7 of set =1.pdf:")
for it in items:
    print(f"y={it[0]:.1f}, x={it[1]:.1f}: '{it[2]}'")

