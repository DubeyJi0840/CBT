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
w, h = img.size

# Let's crop top half: y from 0 to 600
top_half = img.crop((0, 0, w, 600))
res_top, _ = ocr(np.array(top_half))
print(f"Top half (0 to 600) items ({len(res_top) if res_top else 0}):")
for box, text, conf in res_top:
    min_x = min(pt[0] for pt in box)
    min_y = min(pt[1] for pt in box)
    print(f"  y={min_y:.1f}, x={min_x:.1f}: '{text}'")

