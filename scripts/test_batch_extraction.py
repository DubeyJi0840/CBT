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

def preprocess_ocr_lines(raw_items):
    # raw_items: list of (min_y, min_x, text, conf)
    # 1. Fix common OCR mergers of option labels
    fixed_lines = []
    i = 0
    while i < len(raw_items):
        min_y, min_x, text, conf = raw_items[i]
        
        # If line is just a number like "9." or "10." and next line is prompt, combine them
        if re.match(r'^\s*([1-9]\d?|100)[\.\:]?\s*$', text) and i + 1 < len(raw_items):
            q_num_str = re.match(r'^\s*([1-9]\d?|100)', text).group(1)
            next_line = raw_items[i+1][2]
            text = f"{q_num_str}. {next_line}"
            i += 1  # skip next line
            
        # Fix "(AMeans" -> "(A) Means", "(BOnline" -> "(B) Online", etc.
        text = re.sub(r'[\(\[\{]([A-Da-d])([A-Za-z\u0900-\u097F])', r'(\1) \2', text)
        # Fix "A)text" -> "(A) text"
        text = re.sub(r'\b([A-Da-d])\)\s*', r'(\1) ', text)
        # Fix "(A " -> "(A) "
        text = re.sub(r'[\(\[\{]([A-Da-d])\s+', r'(\1) ', text)
        
        fixed_lines.append((min_y, min_x, text, conf))
        i += 1
        
    return fixed_lines

def extract_set(set_id, fname, total_pages, set_title):
    filepath = os.path.join(QUESTIONS_DIR, fname)
    doc = pymupdf.open(filepath)
    ans_key_page_idx = total_pages - 1
    v_map = VERIFIED_KEYS.get(set_id, {})
    
    questions = []
    
    for pno in range(ans_key_page_idx):
        page = doc[pno]
        pix = page.get_pixmap(dpi=150)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        w, h = img.size
        
        # We also do a small crop of header to remove "PRACTICE SET 01" banner
        # Banner is in top 12% on page 0
        y_start_l = int(h * 0.12) if pno == 0 else int(h * 0.05)
        y_start_r = int(h * 0.12) if pno == 0 else int(h * 0.05)
        
        img_l = img.crop((0, y_start_l, int(w * 0.51), int(h * 0.95)))
        img_r = img.crop((int(w * 0.49), y_start_r, w, int(h * 0.95)))
        
        res_l, _ = ocr(np.array(img_l))
        res_r, _ = ocr(np.array(img_r))
        
        for col_idx, (col_name, res_col) in enumerate([('left', res_l), ('right', res_r)]):
            if not res_col: continue
            
            # Sort by Y
            raw_items = []
            for box, text, conf in res_col:
                min_y = min(pt[1] for pt in box)
                min_x = min(pt[0] for pt in box)
                t = text.strip()
                if t and not ('ONLINE SCHOOL' in t.upper() or 'PRACTICE SET' in t.upper()):
                    raw_items.append((min_y, min_x, t, float(conf)))
            raw_items.sort(key=lambda x: x[0])
            
            fixed_items = preprocess_ocr_lines(raw_items)
            
            # Now parse questions
            cur_q = None
            for min_y, min_x, text, conf in fixed_items:
                qm = re.match(r'^\s*([1-9]\d?|100)[\.\:\)]\s*(.*)$', text)
                if qm and not re.match(r'^\s*\(?[A-Da-d]\)', text):
                    qnum = int(qm.group(1))
                    rest = qm.group(2).strip()
                    if cur_q:
                        questions.append(cur_q)
                    cur_q = {
                        'qno': qnum,
                        'page': pno + 1,
                        'col': col_name,
                        'prompt_parts': [rest] if rest else [],
                        'options': {'A': '', 'B': '', 'C': '', 'D': ''},
                        'cur_opt': None
                    }
                    continue
                    
                if cur_q is None:
                    continue
                    
                # Look for option markers
                opt_matches = list(re.finditer(r'\(?([A-Da-d])\)[\.\:\-\s]*', text))
                if opt_matches:
                    first_start = opt_matches[0].start()
                    pre_text = text[:first_start].strip()
                    if pre_text:
                        if cur_q['cur_opt']:
                            cur_q['options'][cur_q['cur_opt']] += " " + pre_text
                        else:
                            cur_q['prompt_parts'].append(pre_text)
                            
                    for i, om in enumerate(opt_matches):
                        let = om.group(1).upper()
                        start_pos = om.end()
                        end_pos = opt_matches[i+1].start() if i+1 < len(opt_matches) else len(text)
                        chunk = text[start_pos:end_pos].strip()
                        cur_q['cur_opt'] = let
                        if cur_q['options'][let]:
                            cur_q['options'][let] += " " + chunk
                        else:
                            cur_q['options'][let] = chunk
                else:
                    if cur_q['cur_opt']:
                        cur_q['options'][cur_q['cur_opt']] += " " + text
                    else:
                        cur_q['prompt_parts'].append(text)
                        
            if cur_q:
                questions.append(cur_q)
                
    doc.close()
    
    # Process and validate
    valid_qs = []
    unverified_qs = []
    
    for q in questions:
        qnum = q['qno']
        prompt = ' '.join(q['prompt_parts']).strip()
        opts = []
        for let in ['A', 'B', 'C', 'D']:
            t = re.sub(r'\s{2,}', ' ', q['options'][let]).strip()
            opts.append({'id': let, 'label': let, 'text': t})
            
        correct_ans = v_map.get(qnum)
        
        # Bilingual split
        en_part = prompt
        hi_part = ""
        if '/' in prompt:
            parts = prompt.split('/')
            en_part = parts[0].strip()
            hi_part = '/'.join(parts[1:]).strip()
            
        is_valid = (
            len(prompt) >= 6 and 
            all(len(o['text']) > 0 for o in opts) and 
            correct_ans in ['A', 'B', 'C', 'D']
        )
        
        q_obj = {
            'id': f"LIS-{set_id.upper()}-Q{qnum:03d}",
            'set_id': set_id,
            'set_title': set_title,
            'source_file': fname,
            'source_page': q['page'],
            'original_question_number': qnum,
            'question_type': 'MCQ',
            'question': prompt,
            'question_en': en_part if en_part else prompt,
            'question_hi': hi_part,
            'options': opts,
            'correct_option': correct_ans,
            'status': 'verified' if is_valid else 'unverified',
            'verification_source': 'Printed Answer Key Table' if correct_ans else None,
            'issue': None if is_valid else f"Missing options or text (found: {[o['id'] for o in opts if len(o['text']) > 0]})"
        }
        
        if is_valid:
            valid_qs.append(q_obj)
        else:
            unverified_qs.append(q_obj)
            
    return valid_qs, unverified_qs

if __name__ == '__main__':
    v1, u1 = extract_set('set_1', 'set =1.pdf', 8, 'Set 01')
    v2, u2 = extract_set('set_2', 'set -2.pdf', 8, 'Set 02')
    print(f"Set 1: Valid={len(v1)}, Unverified={len(u1)}")
    print(f"Set 2: Valid={len(v2)}, Unverified={len(u2)}")

