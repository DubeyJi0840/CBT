import os
import pymupdf
import cv2
import numpy as np
import re
from PIL import Image
import io
from rapidocr_onnxruntime import RapidOCR

QUESTIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'questions')
ocr = RapidOCR()

def find_table_bbox(img_np):
    # Find table bounding box by finding horizontal and vertical lines or the "ANSWER KEY" header
    res, _ = ocr(img_np)
    header_y = None
    for item in res:
        if 'ANSWER' in item[1].upper() or 'KEY' in item[1].upper():
            header_y = max(pt[1] for pt in item[0])
            break
            
    # Also find "100" or bottom row
    bottom_y = None
    for item in res:
        if '100' in item[1]:
            bottom_y = max(pt[1] for pt in item[0])
            
    return header_y, bottom_y

print("Testing table bounding box on Set 1:")
doc = pymupdf.open(os.path.join(QUESTIONS_DIR, 'set =1.pdf'))
pix = doc[7].get_pixmap(dpi=200)
img_np = np.array(Image.open(io.BytesIO(pix.tobytes("png"))))
hy, by = find_table_bbox(img_np)
print(f"Header Y: {hy}, Bottom Y: {by}, height: {by - hy if hy and by else None}")
doc.close()

