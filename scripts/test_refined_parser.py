import os
import pymupdf
import re
import json
import numpy as np
from PIL import Image
import io
from rapidocr_onnxruntime import RapidOCR

from verified_answer_keys import VERIFIED_KEYS

QUESTIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'questions')
ocr = RapidOCR()

def parse_column_refined(res_col, page_no, col_name, verified_map, set_id):
    if not res_col:
        return []
        
    items = []
    for box, text, conf in res_col:
        min_y = min(pt[1] for pt in box)
        min_x = min(pt[0] for pt in box)
        t = text.strip()
        if t:
            items.append((min_y, min_x, t, float(conf)))
            
    items.sort(key=lambda x: x[0])
    
    # We want to tokenize into:
    # - Question Start: Q<num>
    # - Option Start: (A), (B), (C), (D)
    # - Prompt / Option text
    
    # Let's inspect the tokens
    q_re = re.compile(r'\b([1-9]\d?|100)[\.\:]\s*')
    opt_re = re.compile(r'[\(\[\{]?([A-Da-d])[\)\]\}][\.\:\-\s]*')
    
    questions = []
    current_q = None
    
    for min_y, min_x, text, conf in items:
        # Ignore top headers like "PRACTICE SET", "01"
        if text.upper() in ['PRACTICE SET', '01', 'PRACTICE', 'SET'] or 'ONLINE SCHOOL' in text.upper():
            continue
            
        # Check if line contains a question number
        # Note: Question number usually appears near the start of the line, or after a dot
        qm = re.match(r'^(?:[^\w\d]*)([1-9]\d?|100)[\.\:\)]\s*(.*)$', text)
        if qm:
            qnum = int(qm.group(1))
            rest = qm.group(2).strip()
            if current_q:
                questions.append(current_q)
            current_q = {
                'qno': qnum,
                'page': page_no,
                'col': col_name,
                'raw_prompt': [],
                'options': {'A': '', 'B': '', 'C': '', 'D': ''},
                'cur_opt': None
            }
            if rest:
                text = rest
            else:
                continue
                
        if current_q is None:
            # text before any question in this column
            continue
            
        # Now process 'text' which might contain options: (A)... (B)...
        # Find all option markers in 'text'
        # e.g. (A) Libsys (B) Koha or (A) 1914 (B) 1933
        matches = list(re.finditer(r'(?:^|[\s\/\(\[\{])([A-Da-d])[\)\]\}][\.\:\-\s]*', text))
        
        if matches:
            # Check if there is text before the first option marker
            first_start = matches[0].start()
            pre_text = text[:first_start].strip()
            if pre_text:
                if current_q['cur_opt']:
                    current_q['options'][current_q['cur_opt']] += " " + pre_text
                else:
                    current_q['raw_prompt'].append(pre_text)
                    
            for i, m in enumerate(matches):
                opt_letter = m.group(1).upper()
                opt_content_start = m.end()
                opt_content_end = matches[i+1].start() if i+1 < len(matches) else len(text)
                chunk = text[opt_content_start:opt_content_end].strip()
                current_q['cur_opt'] = opt_letter
                current_q['options'][opt_letter] += (" " + chunk if current_q['options'][opt_letter] else chunk)
        else:
            # No option marker on this line
            if current_q['cur_opt']:
                current_q['options'][current_q['cur_opt']] += " " + text
            else:
                current_q['raw_prompt'].append(text)
                
    if current_q:
        questions.append(current_q)
        
    # Post-process questions
    results = []
    for q in questions:
        qnum = q['qno']
        prompt = ' '.join(q['raw_prompt']).strip()
        opts = []
        for let in ['A', 'B', 'C', 'D']:
            t = q['options'][let].strip()
            # Clean trailing punctuation
            t = re.sub(r'[\r\n\t]+', ' ', t).strip()
            opts.append({'id': let, 'label': let, 'text': t})
            
        correct = verified_map.get(qnum)
        is_valid = (
            len(prompt) >= 5 and 
            all(len(o['text']) > 0 for o in opts) and 
            correct in ['A', 'B', 'C', 'D']
        )
        
        results.append({
            'qno': qnum,
            'prompt': prompt,
            'options': opts,
            'correct': correct,
            'is_valid': is_valid
        })
        
    return results

def test_page0():
    doc = pymupdf.open(os.path.join(QUESTIONS_DIR, 'set =1.pdf'))
    page = doc[0]
    pix = page.get_pixmap(dpi=150)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    w, h = img.size
    
    img_l = img.crop((0, 0, int(w * 0.51), h))
    img_r = img.crop((int(w * 0.49), 0, w, h))
    
    res_l, _ = ocr(np.array(img_l))
    res_r, _ = ocr(np.array(img_r))
    
    v_map = VERIFIED_KEYS['set_1']
    qs_l = parse_column_refined(res_l, 1, 'left', v_map, 'set_1')
    qs_r = parse_column_refined(res_r, 1, 'right', v_map, 'set_1')
    
    print("=== Left Column Questions ===")
    for q in qs_l:
        print(f"Q{q['qno']} (valid={q['is_valid']}, ans={q['correct']}): {q['prompt'][:60]}...")
        for o in q['options']:
            print(f"    {o['id']}: {o['text']}")
            
    print("\n=== Right Column Questions ===")
    for q in qs_r:
        print(f"Q{q['qno']} (valid={q['is_valid']}, ans={q['correct']}): {q['prompt'][:60]}...")
        for o in q['options']:
            print(f"    {o['id']}: {o['text']}")
    doc.close()

if __name__ == '__main__':
    test_page0()

