import os
import pymupdf
from rapidocr_onnxruntime import RapidOCR
import numpy as np
from PIL import Image
import io
import re

QUESTIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'questions')

def inspect_qa():
    ocr = RapidOCR()
    qa_path = os.path.join(QUESTIONS_DIR, 'qa.pdf')
    doc = pymupdf.open(qa_path)
    print(f"qa.pdf pages: {len(doc)}")
    
    # Check every page for headings or "PRACTICE SET" or "ANSWER KEY" or table of answers
    for p in range(len(doc)):
        page = doc[p]
        # sample at 100 dpi
        pix = page.get_pixmap(dpi=100)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        res, _ = ocr(np.array(img))
        lines = [r[1] for r in res] if res else []
        joined = " ".join(lines)
        
        # Check headings
        headers = [l for l in lines[:10] if 'PRACTICE' in l.upper() or 'SET' in l.upper() or 'ANSWER' in l.upper() or 'KEY' in l.upper()]
        matches = re.findall(r'\b(\d{1,3})[\.\s\:\-\)]+[\[\(\{\/\\]*([A-Da-d])[\]\)\}\/\\]*', joined)
        
        if headers or len(matches) > 15:
            print(f"Page {p}: headers={headers}, answer_matches={len(matches)}")
            if len(matches) > 15:
                print(f"   Sample keys on page {p}: {matches[:10]}")

    doc.close()

if __name__ == '__main__':
    inspect_qa()

