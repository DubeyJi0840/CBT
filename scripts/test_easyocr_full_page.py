import os
import pymupdf
import easyocr
import time
import numpy as np
from PIL import Image
import io

QUESTIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'questions')
reader = easyocr.Reader(['hi', 'en'], gpu=False)

doc = pymupdf.open(os.path.join(QUESTIONS_DIR, 'set =1.pdf'))
page = doc[0]
pix = page.get_pixmap(dpi=150)
img = Image.open(io.BytesIO(pix.tobytes("png")))
w, h = img.size

t0 = time.time()
# Left col
img_l = img.crop((0, 0, int(w * 0.51), h))
res_l = reader.readtext(np.array(img_l))

# Right col
img_r = img.crop((int(w * 0.49), 0, w, h))
res_r = reader.readtext(np.array(img_r))
t1 = time.time()

print(f"Time for full page (both columns): {t1 - t0:.2f} seconds")
print(f"Left col lines: {len(res_l)}, Right col lines: {len(res_r)}")

print("\n--- Top 15 Left col lines ---")
for bbox, text, prob in res_l[:15]:
    print(f"  [{prob:.2f}] {text}")

print("\n--- Top 15 Right col lines ---")
for bbox, text, prob in res_r[:15]:
    print(f"  [{prob:.2f}] {text}")

doc.close()

