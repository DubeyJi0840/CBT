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
pix = page.get_pixmap(dpi=300)
img = Image.open(io.BytesIO(pix.tobytes("png")))

# Let's crop x from 0 to 1400, y from 0 to 500
box_crop = img.crop((0, 0, 1400, 500))
res, _ = ocr(np.array(box_crop))
print(f"Top-left region items ({len(res) if res else 0}):")
for box, text, conf in res:
    min_x = min(pt[0] for pt in box)
    min_y = min(pt[1] for pt in box)
    print(f"  y={min_y:.1f}, x={min_x:.1f}: '{text}' (conf: {float(conf):.2f})")

