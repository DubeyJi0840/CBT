import os
import sys
import pymupdf
import re
import json
import numpy as np
from PIL import Image
import io
from rapidocr_onnxruntime import RapidOCR

from verified_answer_keys import VERIFIED_KEYS

QUESTIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'questions')
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

ocr = RapidOCR()

SET_CONFIG = [
    ('set_1', 'set =1.pdf', 8, 'Set 01'),
    ('set_2', 'set -2.pdf', 8, 'Set 02'),
    ('set_3', 'set -3.pdf', 8, 'Set 03'),
    ('set_4', 'set -4.pdf', 8, 'Set 04'),
    ('set_5', 'set -5.pdf', 9, 'Set 05'),
    ('set_6', 'set-6.pdf', 9, 'Set 06'),
    ('set_7', 'set-7.pdf', 10, 'Set 07'),
    ('set_8', 'set 8.pdf', 9, 'Set 08'),
    ('set_9', 'set 9.pdf', 9, 'Set 09'),
    ('set_10', 'set 10.pdf', 9, 'Set 10')
]

def clean_text(t):
    t = re.sub(r'[\r\n]+', ' ', t)
    t = re.sub(r'\s{2,}', ' ', t)
    return t.strip()

def split_bilingual(text):
    # If text contains '/', often 'English / Hindi'
    parts = text.split('/')
    if len(parts) >= 2:
        en = clean_text(parts[0])
        hi = clean_text('/'.join(parts[1:]))
        return en, hi
    return clean_text(text), clean_text(text)

def parse_column_boxes(res_col, page_no, col_name, verified_map, set_id, set_title, fname):
    if not res_col:
        return []
        
    # Sort boxes top to bottom
    items = []
    for box, text, conf in res_col:
        min_y = min(pt[1] for pt in box)
        min_x = min(pt[0] for pt in box)
        t = text.strip()
        if t:
            items.append((min_y, min_x, t, float(conf)))
            
    items.sort(key=lambda x: x[0])
    
    # We want to group items into questions
    # Question header regex: e.g. "1.", "1. ", "10.", "95."
    # Option markers: "(A)", "(B)", "(C)", "(D)", "1(A)", etc.
    q_pattern = re.compile(r'^(\d{1,3})[\.\s\:\-\)]+\s*(.*)$')
    opt_start = re.compile(r'^\(?([A-Da-d])\)?[\.\:\-\s]+(.*)$')
    
    parsed_questions = []
    current_qno = None
    prompt_lines = []
    options = {}
    current_opt = None
    
    def finalize_current():
        nonlocal current_qno, prompt_lines, options, current_opt
        if current_qno is not None:
            full_prompt = clean_text(' '.join(prompt_lines))
            # Clean options
            opts_clean = []
            for letter in ['A', 'B', 'C', 'D']:
                if letter in options:
                    opts_clean.append({
                        'id': letter,
                        'label': letter,
                        'text': clean_text(options[letter])
                    })
                    
            correct_ans = verified_map.get(current_qno)
            en_text, hi_text = split_bilingual(full_prompt)
            
            is_valid = (
                len(full_prompt) >= 5 and 
                len(opts_clean) == 4 and 
                all(len(o['text']) > 0 for o in opts_clean) and 
                correct_ans in ['A', 'B', 'C', 'D']
            )
            
            parsed_questions.append({
                'id': f"LIS-{set_id.upper()}-Q{current_qno:03d}",
                'set_id': set_id,
                'set_title': set_title,
                'source_file': fname,
                'source_page': page_no,
                'question_number': current_qno,
                'question': full_prompt,
                'question_en': en_text,
                'question_hi': hi_text,
                'options': opts_clean,
                'correct_option': correct_ans,
                'is_valid': is_valid,
                'status': 'verified' if is_valid else 'unverified',
                'verification_source': 'Printed Answer Key Table' if correct_ans else None,
                'issue': None if is_valid else f"Missing options or prompt (found {len(opts_clean)} options)"
            })
            
        current_qno = None
        prompt_lines = []
        options = {}
        current_opt = None

    for min_y, min_x, text, conf in items:
        # Check if line contains inline options like (A)... (B)...
        # First check question start
        qm = q_pattern.match(text)
        # Check that it's a valid question number between 1 and 100
        if qm and 1 <= int(qm.group(1)) <= 100 and not re.match(r'^[A-Da-d]\)', text):
            candidate_num = int(qm.group(1))
            # If line is just like "1. 1914" it might be an option with number? In our PDF, questions have 1. 2. 3.
            # But let's check if we already have an active question with options A,B,C,D
            finalize_current()
            current_qno = candidate_num
            rest = qm.group(2).strip()
            if rest:
                # check if rest has (A)
                opt_matches = list(re.finditer(r'\(?([A-Da-d])\)[\.\:\-\s]+', rest))
                if opt_matches:
                    first_opt_idx = opt_matches[0].start()
                    p_part = rest[:first_opt_idx].strip()
                    if p_part: prompt_lines.append(p_part)
                    # parse remaining options on this line
                    for i, om in enumerate(opt_matches):
                        let = om.group(1).upper()
                        start_pos = om.end()
                        end_pos = opt_matches[i+1].start() if i+1 < len(opt_matches) else len(rest)
                        options[let] = rest[start_pos:end_pos].strip()
                        current_opt = let
                else:
                    prompt_lines.append(rest)
            continue
            
        # If not a new question, check if it starts with an option letter
        # Handles lines like "(A) Libsys", "(B) Koha (C) SOUL", etc.
        opt_matches = list(re.finditer(r'\(?([A-Da-d])\)[\.\:\-\s]+', text))
        if opt_matches and current_qno is not None:
            # Check if there is text before first option
            first_idx = opt_matches[0].start()
            if first_idx > 0 and not current_opt:
                prefix = text[:first_idx].strip()
                if prefix: prompt_lines.append(prefix)
                
            for i, om in enumerate(opt_matches):
                let = om.group(1).upper()
                start_pos = om.end()
                end_pos = opt_matches[i+1].start() if i+1 < len(opt_matches) else len(text)
                options[let] = text[start_pos:end_pos].strip()
                current_opt = let
        elif current_qno is not None:
            # Continuation of either question prompt or current option
            if current_opt and current_opt in options:
                options[current_opt] += " " + text
            else:
                prompt_lines.append(text)
                
    finalize_current()
    return parsed_questions

def process_set(set_id, fname, total_pages, set_title):
    filepath = os.path.join(QUESTIONS_DIR, fname)
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return []
        
    doc = pymupdf.open(filepath)
    ans_key_page_idx = total_pages - 1
    verified_map = VERIFIED_KEYS.get(set_id, {})
    
    set_questions = []
    
    # Process question pages (exclude the last page with answer key)
    for pno in range(ans_key_page_idx):
        page = doc[pno]
        pix = page.get_pixmap(dpi=150)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        w, h = img.size
        
        # Crop left and right columns
        img_left = img.crop((0, 0, int(w * 0.51), h))
        img_right = img.crop((int(w * 0.49), 0, w, h))
        
        res_l, _ = ocr(np.array(img_left))
        res_r, _ = ocr(np.array(img_right))
        
        qs_l = parse_column_boxes(res_l, pno + 1, 'left', verified_map, set_id, set_title, fname)
        qs_r = parse_column_boxes(res_r, pno + 1, 'right', verified_map, set_id, set_title, fname)
        
        set_questions.extend(qs_l)
        set_questions.extend(qs_r)
        
    doc.close()
    return set_questions

def run_extraction(target_sets=None):
    all_extracted = []
    sets_to_run = SET_CONFIG if not target_sets else [s for s in SET_CONFIG if s[0] in target_sets]
    
    for set_id, fname, total_pages, set_title in sets_to_run:
        print(f"\nProcessing {set_title} ({fname}, {total_pages} pages)...")
        qs = process_set(set_id, fname, total_pages, set_title)
        valid_count = sum(1 for q in qs if q['is_valid'])
        print(f"  -> Extracted {len(qs)} raw items, {valid_count} valid verified MCQs")
        all_extracted.extend(qs)
        
    return all_extracted

if __name__ == '__main__':
    # Test on Set 1, Set 2, Set 3 first
    res = run_extraction(['set_1', 'set_2', 'set_3'])
    valid_total = sum(1 for q in res if q['is_valid'])
    print(f"\n=== SUMMARY ===")
    print(f"Total extracted: {len(res)}, Valid MCQs: {valid_total}")
    with open('test_extracted.json', 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print("Saved test_extracted.json")

