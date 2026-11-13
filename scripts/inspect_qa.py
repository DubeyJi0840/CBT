import os
import pymupdf
from rapidocr_onnxruntime import RapidOCR
import numpy as np
from PIL import Image
import io

QUESTIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'questions')

def inspect_qa_and_sets():
    ocr = RapidOCR()
    
    # Check qa.pdf page 0 and page 1
    doc_qa = pymupdf.open(os.path.join(QUESTIONS_DIR, 'qa.pdf'))
    print(f"qa.pdf total pages: {len(doc_qa)}")
    for p in [0, 1, 87]:
        page = doc_qa[p]
        pix = page.get_pixmap(dpi=150)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        res, _ = ocr(np.array(img))
        print(f"\n--- qa.pdf page {p} ({len(res) if res else 0} lines) ---")
        if res:
            for item in res[:10]:
                print(f"  {item[1]}")
    doc_qa.close()

if __name__ == '__main__':
    inspect_qa_and_sets()

