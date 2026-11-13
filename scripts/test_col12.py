import os
import pymupdf
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

# Let's crop Col 1 top: x in [150, 450], y in [300, 550]
c1 = img.crop((150, 300, 450, 550))
r1, _ = ocr(np.array(c1))
print("Col 1 top:")
for r in (r1 or []):
    print("  ", r[1])

# Let's crop Col 2 top: x in [550, 850], y in [300, 550]
c2 = img.crop((550, 300, 850, 550))
r2, _ = ocr(np.array(c2))
print("Col 2 top:")
for r in (r2 or []):
    print("  ", r[1])

