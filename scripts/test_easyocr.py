import os
import pymupdf
import easyocr
import numpy as np
from PIL import Image
import io

QUESTIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'questions')
reader = easyocr.Reader(['hi', 'en'], gpu=False)

# Test on page 0 of set =1.pdf, cropping question 1 and question 9
doc = pymupdf.open(os.path.join(QUESTIONS_DIR, 'set =1.pdf'))
page = doc[0]
pix = page.get_pixmap(dpi=150)
img = Image.open(io.BytesIO(pix.tobytes("png")))
w, h = img.size

# Crop question 1 on right column: x in [w//2, w], y in [300, 500]
crop_q1 = img.crop((int(w * 0.5), 300, w, 500))
res_q1 = reader.readtext(np.array(crop_q1))

print("=== EasyOCR Q1 (Hindi + English) ===")
for bbox, text, prob in res_q1:
    print(f"  [{prob:.2f}] {text}")

doc.close()

