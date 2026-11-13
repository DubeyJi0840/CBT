import os
import pymupdf
from rapidocr_onnxruntime import RapidOCR
import numpy as np
from PIL import Image
import io

QUESTIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'questions')

ocr = RapidOCR()
def get_ocr_lines(page):
    pix = page.get_pixmap(dpi=150)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    res, _ = ocr(np.array(img))
    return [r[1] for r in res] if res else []

doc1 = pymupdf.open(os.path.join(QUESTIONS_DIR, 'set =1.pdf'))
doc_qa = pymupdf.open(os.path.join(QUESTIONS_DIR, 'qa.pdf'))

print("=== set =1.pdf Page 0 ===")
lines1 = get_ocr_lines(doc1[0])
for l in lines1[:15]:
    print("  ", l)

print("\n=== qa.pdf Page 0 ===")
lines_qa0 = get_ocr_lines(doc_qa[0])
for l in lines_qa0[:15]:
    print("  ", l)

print("\n=== qa.pdf Page 1 ===")
lines_qa1 = get_ocr_lines(doc_qa[1])
for l in lines_qa1[:15]:
    print("  ", l)

