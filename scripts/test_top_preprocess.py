import os
import pymupdf
import cv2
import numpy as np
from PIL import Image
import io
from rapidocr_onnxruntime import RapidOCR

QUESTIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'questions')
ocr = RapidOCR()

doc = pymupdf.open(os.path.join(QUESTIONS_DIR, 'set =1.pdf'))
page = doc[7]
pix = page.get_pixmap(dpi=300)
img = Image.open(io.BytesIO(pix.tobytes("png")))
crop = img.crop((0, 0, 1500, 600))
crop_np = np.array(crop)

# Let's try different preprocessings
gray = cv2.cvtColor(crop_np, cv2.COLOR_RGB2GRAY)
_, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
res_thresh, _ = ocr(thresh)
print("Thresh results:")
for r in res_thresh:
    print("  ", r[1])

# Also check without thresholding on smaller boxes
print("\nTesting 200-pixel slices:")
for y_start in [100, 200, 300, 400]:
    slice_img = crop_np[y_start:y_start+150, :]
    res_s, _ = ocr(slice_img)
    if res_s:
        for r in res_s:
            print(f"  y_slice={y_start}: {r[1]}")

