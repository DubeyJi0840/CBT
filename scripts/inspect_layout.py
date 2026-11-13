import os
import pymupdf
from rapidocr_onnxruntime import RapidOCR
import numpy as np
from PIL import Image
import io

QUESTIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'questions')

ocr = RapidOCR()
doc = pymupdf.open(os.path.join(QUESTIONS_DIR, 'set =1.pdf'))
page = doc[0]
pix = page.get_pixmap(dpi=150)
img = Image.open(io.BytesIO(pix.tobytes("png")))
w, h = img.size
print(f"Image size: width={w}, height={h}")

res, _ = ocr(np.array(img))
# Each item in res: [box, text, score]
# box is [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
boxes_with_text = []
for box, text, score in res:
    xs = [pt[0] for pt in box]
    ys = [pt[1] for pt in box]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    center_x = (min_x + max_x) / 2
    boxes_with_text.append((center_x, min_y, min_x, max_x, max_y, text, score))

print("\nLeft column items (center_x < w/2):")
left_col = [b for b in boxes_with_text if b[0] < w * 0.5]
left_col.sort(key=lambda b: b[1])  # sort by y
for b in left_col[:25]:
    print(f"  y={b[1]:.1f}, x={b[2]:.1f}-{b[3]:.1f}: {b[5]}")

print("\nRight column items (center_x >= w/2):")
right_col = [b for b in boxes_with_text if b[0] >= w * 0.5]
right_col.sort(key=lambda b: b[1])  # sort by y
for b in right_col[:25]:
    print(f"  y={b[1]:.1f}, x={b[2]:.1f}-{b[3]:.1f}: {b[5]}")

