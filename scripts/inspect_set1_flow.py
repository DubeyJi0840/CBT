import os
import pymupdf
from rapidocr_onnxruntime import RapidOCR
import numpy as np
from PIL import Image
import io
import re

QUESTIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'questions')

ocr = RapidOCR()

def inspect_set1_questions():
    doc = pymupdf.open(os.path.join(QUESTIONS_DIR, 'set =1.pdf'))
    for pno in range(len(doc)):
        page = doc[pno]
        pix = page.get_pixmap(dpi=150)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        w, h = img.size
        
        # We can run OCR on left half and right half separately!
        # Left half: [0, 0, w//2, h]
        # Right half: [w//2, 0, w, h]
        img_left = img.crop((0, 0, int(w * 0.52), h))
        img_right = img.crop((int(w * 0.48), 0, w, h))
        
        res_l, _ = ocr(np.array(img_left))
        res_r, _ = ocr(np.array(img_right))
        
        lines_l = [r[1] for r in res_l] if res_l else []
        lines_r = [r[1] for r in res_r] if res_r else []
        
        q_l = [l for l in lines_l if re.match(r'^\d{1,3}[\.\s]', l)]
        q_r = [l for l in lines_r if re.match(r'^\d{1,3}[\.\s]', l)]
        
        print(f"Page {pno}:")
        print(f"  Left col detected Q numbers: {q_l}")
        print(f"  Right col detected Q numbers: {q_r}")

inspect_set1_questions()

