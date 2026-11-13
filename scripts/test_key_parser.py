import os
import pymupdf
from rapidocr_onnxruntime import RapidOCR
import numpy as np
from PIL import Image
import io
import re

QUESTIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'questions')
ocr = RapidOCR()

doc = pymupdf.open(os.path.join(QUESTIONS_DIR, 'set =1.pdf'))
page = doc[-1] # last page
pix = page.get_pixmap(dpi=200) # higher dpi for table
img = Image.open(io.BytesIO(pix.tobytes("png")))
res, _ = ocr(np.array(img))

key_dict = {}
# res is list of [box, text, conf]
# Sort by box y then x, or sort into table columns
boxes = []
for box, text, conf in res:
    # bounding box
    min_x = min(pt[0] for pt in box)
    min_y = min(pt[1] for pt in box)
    boxes.append((min_y, min_x, text, conf))

# Let's inspect raw text tokens
for item in boxes:
    t = item[2].strip()
    # Find patterns like "1. [A]" or "1 [A]" or "1. A" or "1.(A)" or "1-A"
    m = re.search(r'\b(\d{1,3})[\.\s\:\-\)]+[\(\[\{\/\\]*([A-Da-d])[\)\]\}\/\\]*', t)
    if m:
        qnum = int(m.group(1))
        ans = m.group(2).upper()
        if 1 <= qnum <= 100:
            key_dict[qnum] = ans
    else:
        # Also check if text is just like "1.A" or "1A"
        m2 = re.search(r'^(\d{1,3})([A-Da-d])$', t)
        if m2:
            qnum = int(m2.group(1))
            ans = m2.group(2).upper()
            if 1 <= qnum <= 100:
                key_dict[qnum] = ans

print(f"Set 1: Extracted {len(key_dict)} answers out of 100:")
missing = [i for i in range(1, 101) if i not in key_dict]
print(f"Missing numbers: {missing}")
print(f"Keys 1..20: {[(i, key_dict.get(i)) for i in range(1, 21)]}")

