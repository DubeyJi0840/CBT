import os
import pymupdf
import re
import numpy as np
from PIL import Image
import io
from rapidocr_onnxruntime import RapidOCR

QUESTIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'questions')
ocr = RapidOCR()

def parse_column_lines(lines, page_num, col_name):
    questions = []
    current_q = None
    
    # regex for question start: e.g. "1.", "1 ", "12. ", "100."
    q_pattern = re.compile(r'^(\d{1,3})[\.\s\:\-\)]+\s*(.*)$')
    # regex for option: e.g. "(A)", "(B)", "(C)", "(D)", "A)", "A."
    opt_pattern = re.compile(r'^\(?([A-Da-d])\)?[\.\:\-\s]+(.*)$')
    # regex for inline options: e.g. "(A) 1914 (B) 1933"
    inline_opt_pattern = re.compile(r'\(?([A-Da-d])\)?[\.\:\-\s]+([^\(\)]+)')
    
    for line in lines:
        qm = q_pattern.match(line)
        if qm:
            num = int(qm.group(1))
            rest = qm.group(2).strip()
            # If rest contains question text or options
            if current_q:
                questions.append(current_q)
            current_q = {
                'qno': num,
                'raw_lines': [rest] if rest else [],
                'page': page_num,
                'col': col_name
            }
        elif current_q is not None:
            current_q['raw_lines'].append(line)
            
    if current_q:
        questions.append(current_q)
        
    return questions

def test():
    doc = pymupdf.open(os.path.join(QUESTIONS_DIR, 'set =1.pdf'))
    page = doc[0] # Page 1
    pix = page.get_pixmap(dpi=150)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    w, h = img.size
    
    img_l = img.crop((0, 0, int(w * 0.51), h))
    img_r = img.crop((int(w * 0.49), 0, w, h))
    
    res_l, _ = ocr(np.array(img_l))
    res_r, _ = ocr(np.array(img_r))
    
    lines_l = [item[1].strip() for item in sorted(res_l, key=lambda x: min(pt[1] for pt in x[0]))] if res_l else []
    lines_r = [item[1].strip() for item in sorted(res_r, key=lambda x: min(pt[1] for pt in x[0]))] if res_r else []
    
    qs_l = parse_column_lines(lines_l, 1, 'left')
    qs_r = parse_column_lines(lines_r, 1, 'right')
    
    print(f"Page 1 Left detected Qs: {[q['qno'] for q in qs_l]}")
    for q in qs_l:
        print(f"  Q{q['qno']}: {' | '.join(q['raw_lines'][:3])}")
        
    print(f"\nPage 1 Right detected Qs: {[q['qno'] for q in qs_r]}")
    for q in qs_r:
        print(f"  Q{q['qno']}: {' | '.join(q['raw_lines'][:3])}")
    doc.close()

if __name__ == '__main__':
    test()

