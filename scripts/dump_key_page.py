import os
import pymupdf
from rapidocr_onnxruntime import RapidOCR
import numpy as np
from PIL import Image
import io

QUESTIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'questions')
ocr = RapidOCR()

doc = pymupdf.open(os.path.join(QUESTIONS_DIR, 'set =1.pdf'))
page = doc[-1]
pix = page.get_pixmap(dpi=200)
img = Image.open(io.BytesIO(pix.tobytes("png")))
res, _ = ocr(np.array(img))

items = []
for box, text, conf in res:
    min_x = min(pt[0] for pt in box)
    min_y = min(pt[1] for pt in box)
    max_x = max(pt[0] for pt in box)
    max_y = max(pt[1] for pt in box)
    items.append((min_x, min_y, max_x, max_y, text, conf))

# Sort by X first (column) then Y
items.sort(key=lambda it: (it[0] // 200, it[1]))

for it in items:
    print(f"x={it[0]:.1f}, y={it[1]:.1f}: '{it[4]}' (conf: {float(it[5]):.2f})")
