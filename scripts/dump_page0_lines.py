import os
import pymupdf
import numpy as np
from PIL import Image
import io
from rapidocr_onnxruntime import RapidOCR

QUESTIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'questions')
ocr = RapidOCR()

doc = pymupdf.open(os.path.join(QUESTIONS_DIR, 'set =1.pdf'))
page = doc[0]
pix = page.get_pixmap(dpi=150)
img = Image.open(io.BytesIO(pix.tobytes("png")))
w, h = img.size

img_left = img.crop((0, 0, int(w * 0.51), h))
img_right = img.crop((int(w * 0.49), 0, w, h))

res_l, _ = ocr(np.array(img_left))
res_r, _ = ocr(np.array(img_right))

print("=== LEFT COLUMN LINES ===")
if res_l:
    res_l.sort(key=lambda item: min(pt[1] for pt in item[0]))
    for item in res_l:
        min_y = min(pt[1] for pt in item[0])
        print(f"  y={min_y:.1f}: {item[1]}")

print("\n=== RIGHT COLUMN LINES ===")
if res_r:
    res_r.sort(key=lambda item: min(pt[1] for pt in item[0]))
    for item in res_r:
        min_y = min(pt[1] for pt in item[0])
        print(f"  y={min_y:.1f}: {item[1]}")

