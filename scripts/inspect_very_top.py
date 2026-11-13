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
pix = page.get_pixmap(dpi=300) # 300 DPI for high detail!
img = Image.open(io.BytesIO(pix.tobytes("png")))
w, h = img.size

# Let's crop very top: y from 0 to int(h * 0.25)
crop_top = img.crop((0, 0, w, int(h * 0.25)))
res_top, _ = ocr(np.array(crop_top))
print(f"Top 25% at 300 DPI ({len(res_top) if res_top else 0} items):")
for box, text, conf in res_top:
    min_x = min(pt[0] for pt in box)
    min_y = min(pt[1] for pt in box)
    print(f"  y={min_y:.1f}, x={min_x:.1f}: '{text}' (conf: {float(conf):.2f})")

