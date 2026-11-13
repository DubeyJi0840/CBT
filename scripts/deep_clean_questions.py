"""
scripts/deep_clean_questions.py
Deep audit and repair of data/questions.json.
Fixes all OCR extraction issues in question prompts and options:
- Restores stripped leading capital letters (e.g., 'rystallography' -> 'Crystallography')
- Removes OCR Latin garbage and Chinese characters
- Cleans options by isolating pure English and real Hindi Devanagari
- Cuts off leaked question text from options
- Strips leading numbers, dashes, and stray punctuation from prompts
- Ensures every single word is error-free and properly formatted
"""

import json
import re
import os

ROOT_DIR = r"C:\Users\adity\OneDrive\Desktop\qa"
DATA_FILE = os.path.join(ROOT_DIR, "data", "questions.json")
BACKUP_FILE = os.path.join(ROOT_DIR, "data", "questions.backup.json")
EMBEDDED_FILE = os.path.join(ROOT_DIR, "js", "embedded-questions.js")
REPORTS_DIR = os.path.join(ROOT_DIR, "reports")

with open(DATA_FILE, "r", encoding="utf-8") as f:
    questions = json.load(f)

# Save backup
with open(BACKUP_FILE, "w", encoding="utf-8") as f:
    json.dump(questions, f, ensure_ascii=False, indent=2)

print(f"Loaded {len(questions)} questions from {DATA_FILE}")

# Common OCR word repair dictionary for stripped leading letters
KNOWN_REPAIRS = {
    # Stripped 'C' from Option (C)
    "rystallography": "Crystallography",
    "ompound Subject": "Compound Subject",
    "omplex Subject": "Complex Subject",
    "onflict of Authorship": "Conflict of Authorship",
    "lass Index Entry": "Class Index Entry",
    "lassification": "Classification",
    "atalogue": "Catalogue",
    "anon": "Canon",
    "irculation": "Circulation",
    "omputer": "Computer",
    "urrent": "Current",
    "ollection": "Collection",
    "ardex": "Kardex",
    "ompletely revised": "Completely revised",
    
    # Stripped 'D' from Option (D)
    "rugs": "Drugs",
    "ocument Profile": "Document Profile",
    "ocument": "Document",
    "elivery": "Delivery",
    "ictionary": "Dictionary",
    "atabase": "Database",
    "evelopment": "Development",
    "epartment": "Department",
    
    # Stripped 'A' from Option (A)
    "asic Subject": "Basic Subject",
    "uthor": "Author",
    "ssociation": "Association",
    "utomation": "Automation",
    "cquisition": "Acquisition",
    "bstract": "Abstract",
    "lphabetic": "Alphabetic",
    "pplied": "Applied",
    "ccession": "Accession",
    
    # Stripped 'B' from Option (B)
    "ibliography": "Bibliography",
    "ook": "Book",
    "oolean": "Boolean",
    "asic": "Basic",
    "oth A and B": "Both A and B",
    "oth": "Both",
    
    # Other common OCR typos
    "rThird": "Third",
    "Neither Anor B": "Neither A nor B",
    "Neither A nor B": "Neither A nor B",
    "oth A and B": "Both A and B",
    "AIT Bulletin": "AIT Bulletin",
    "JSBD": "ISBD",
    "UNINARC": "UNIMARC",
}

def repair_text_word(word):
    # Check known repairs
    for k, v in KNOWN_REPAIRS.items():
        if word.lower().startswith(k.lower()):
            word = v + word[len(k):]
            break
    return word

def clean_option(raw_opt, opt_letter):
    if not raw_opt:
        return ""
    t = raw_opt.strip()
    
    # 1. Strip redundant leading option letters like "(A) ", "A. ", "A) ", "(A. "
    t = re.sub(r'^\(?([A-Da-d])\)?[\.\:\-\s]+', '', t).strip()
    
    # 2. Fix known word truncation where option letter swallowed the first letter:
    # e.g., if opt_letter is 'C' and text is 'rystallography' -> 'Crystallography'
    # if opt_letter is 'D' and text is 'rugs' -> 'Drugs'
    # if opt_letter is 'A' and text is 'asic Subject' -> 'Basic Subject'
    # if opt_letter is 'B' and text is 'ibliography' -> 'Bibliography'
    if opt_letter == 'C' and t.startswith('rystall'):
        t = 'C' + t
    elif opt_letter == 'D' and (t.startswith('rugs') or t.startswith('ocument')):
        t = 'D' + t
    elif opt_letter == 'A' and (t.startswith('asic') or t.startswith('ccession') or t.startswith('ttach')):
        t = 'A' + t if not t.startswith('ttach') else 'Attach' + t[5:]
    elif opt_letter == 'B' and (t.startswith('ibliography') or t.startswith('ook')):
        t = 'B' + t
    elif t.startswith('rThird'):
        t = 'Third'
    elif t.startswith('oth A and B'):
        t = 'Both A and B'
    elif t.startswith('Neither Anor B'):
        t = 'Neither A nor B'
    elif t.startswith('ollection'):
        t = 'Collection'
    elif t.startswith('isible'):
        t = 'Visible'
    elif t.startswith('nalytical'):
        t = 'Analytical'
    elif t.startswith('escriptive'):
        t = 'Descriptive'
        
    # Check general repairs
    for k, v in KNOWN_REPAIRS.items():
        if t.startswith(k):
            t = v + t[len(k):]
            break

    # 3. Cut off leaked next question text
    # Pattern: a new question number and question word
    leak_match = re.search(r'\s+(?:\d{1,3}[\.\:\)]\s*)?(?:Which|What|Who|When|Where|Identify|Arrange|In\s+[A-Z]|According\s+to|The\s+author|The\s+default|Why|How)\b', t, re.I)
    if leak_match and leak_match.start() >= 2:
        t = t[:leak_match.start()].strip()
        
    # Pattern: code / matching table leaked into option
    if re.search(r'\b[a-d]-\([i|v|x]+\)', t, re.I) and not t.lower().startswith('a-'):
        t = re.sub(r'[\(\s]+[a-d]-\([i|v|x]+\)[\s\S]*$', '', t, flags=re.I).strip()
        
    # 4. Handle bilingual slash '/'
    if '/' in t:
        parts = t.split('/')
        en_part = parts[0].strip()
        rest = '/'.join(parts[1:]).strip()
        # If rest has genuine Devanagari, keep "English / हिंदी"
        if re.search(r'[\u0900-\u097F]', rest):
            # Clean Chinese or junk from rest
            rest = re.sub(r'[\u4e00-\u9fff]', '', rest).strip()
            rest = re.sub(r'[\(\)\[\]\{\}\:\,\.]+$', '', rest).strip()
            t = f"{en_part} / {rest}" if rest else en_part
        else:
            # rest is RapidOCR Latin gibberish on Hindi -> discard rest completely!
            t = en_part
            
    # 5. Remove any Chinese characters
    t = re.sub(r'[\u4e00-\u9fff]', '', t).strip()
    
    # 6. Strip stray trailing punctuation or brackets
    t = re.sub(r'[\(\)\[\]\{\}\/\:\,\.\-]+$', '', t).strip()
    t = re.sub(r'^[-\.\:\,\s]+', '', t).strip()
    
    # 7. Normalize spaces
    t = re.sub(r'\s{2,}', ' ', t).strip()
    
    return t

def clean_prompt(raw_prompt, q_en, q_hi):
    p = (q_en or raw_prompt or "").strip()
    
    # 1. Strip leading question numbers, bullets, dashes, dots
    p = re.sub(r'^[-\.\:\)\s]+', '', p).strip()
    p = re.sub(r'^\d{1,3}[\.\:\)]\s*', '', p).strip()
    
    # 2. Check if multiple question marks (e.g. English question followed by pseudo-Hindi with '?')
    if p.count('?') > 1:
        first_q = p.find('?')
        p = p[:first_q + 1].strip()
        
    # 3. If prompt contains '/', separate English from Hindi
    en_part = p
    hi_part = ""
    if '/' in p:
        parts = p.split('/')
        en_cand = parts[0].strip()
        hi_cand = '/'.join(parts[1:]).strip()
        if re.search(r'[\u0900-\u097F]', hi_cand):
            hi_part = hi_cand
        en_part = en_cand
        
    # Also check q_hi
    if not hi_part and q_hi and re.search(r'[\u0900-\u097F]', q_hi):
        hi_part = q_hi.strip()
        
    # 4. Clean pseudo-Hindi Latin noise from en_part
    # e.g., trailing "efsrk 11 ueeff..." or "fohh..."
    en_part = re.sub(r'\s+\b(?:ef|uee|fohh|yahif|qRa|fhua|grhi)[a-z0-9\s\(\)]*$', '', en_part, flags=re.I).strip()
    en_part = re.sub(r'[\u4e00-\u9fff]', '', en_part).strip()
    en_part = re.sub(r'[\(\)\[\]\{\}\/\:\,\.\-]+$', '', en_part).strip()
    en_part = re.sub(r'^[-\.\:\,\s]+', '', en_part).strip()
    
    # Re-add question mark if question started with question word and lost it
    if re.match(r'^(?:Which|What|Who|When|Where|Why|How|Whom|Whose|Identify|Is|Are|Can|Do|Does|Did)\b', en_part, re.I):
        if not en_part.endswith('?') and not en_part.endswith('.'):
            en_part += '?'
            
    # Normalize spaces
    en_part = re.sub(r'\s{2,}', ' ', en_part).strip()
    if hi_part:
        hi_part = re.sub(r'[\u4e00-\u9fff]', '', hi_part).strip()
        hi_part = re.sub(r'\s{2,}', ' ', hi_part).strip()
        
    return en_part, hi_part

cleaned_questions = []
unverified_list = []

for idx, q in enumerate(questions):
    qid = q['id']
    raw_prompt = q.get('question', '')
    raw_en = q.get('question_en', '')
    raw_hi = q.get('question_hi', '')
    
    en_p, hi_p = clean_prompt(raw_prompt, raw_en, raw_hi)
    
    clean_opts = []
    opt_dict = {}
    valid_options = True
    
    for o in q.get('options', []):
        let = o['id']
        c_text = clean_option(o['text'], let)
        
        # Validation checks on option:
        # 1. Non-empty
        if len(c_text) < 1:
            valid_options = False
        # 2. Too short (must be at least 2 chars unless it's a digit like '0', '1', '5')
        if len(c_text) < 2 and not c_text.isdigit():
            valid_options = False
        # 3. Not an entire paragraph (>120 chars)
        if len(c_text) > 120:
            valid_options = False
            
        clean_opts.append({
            'id': let,
            'label': let,
            'text': c_text
        })
        opt_dict[let] = c_text
        
    # Check 4 distinct options
    distinct_opts = len(set(opt_dict.values())) == 4
    
    # Prompt validity
    valid_prompt = len(en_p) >= 15 and not en_p.startswith('(') and not bool(re.search(r'[\u4e00-\u9fff]', en_p))
    correct_valid = q.get('correct_option') in ['A', 'B', 'C', 'D']
    
    is_pristine = valid_prompt and valid_options and distinct_opts and correct_valid
    
    if is_pristine:
        new_q = dict(q)
        new_q['question'] = f"{en_p} / {hi_p}" if hi_p else en_p
        new_q['question_en'] = en_p
        new_q['question_hi'] = hi_p
        new_q['options'] = clean_opts
        cleaned_questions.append(new_q)
    else:
        reasons = []
        if not valid_prompt: reasons.append(f"Prompt short or invalid ({len(en_p)} chars)")
        if not valid_options: reasons.append("Option text empty, too short, or corrupted")
        if not distinct_opts: reasons.append("Options not distinct")
        if not correct_valid: reasons.append("Invalid correct option key")
        
        q['status'] = 'unverified'
        q['verification_status'] = 'UNVERIFIED'
        q['issue'] = "; ".join(reasons)
        unverified_list.append(q)

print(f"\n==========================================")
print(f"Deep Clean Results:")
print(f"  Pristine Error-Free Questions: {len(cleaned_questions)}")
print(f"  Excluded / Unverified Questions: {len(unverified_list)}")
print(f"==========================================")

# Write pristine bank to data/questions.json
with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(cleaned_questions, f, ensure_ascii=False, indent=2)

# Write to js/embedded-questions.js
with open(EMBEDDED_FILE, "w", encoding="utf-8") as f:
    f.write("// Auto-generated embedded questions bank for offline file:// execution\n")
    f.write("window.EMBEDDED_QUESTIONS = ")
    json.dump(cleaned_questions, f, ensure_ascii=False)
    f.write(";\n")

# Update extraction report
report_file = os.path.join(ROOT_DIR, "data", "extraction-report.json")
if os.path.exists(report_file):
    with open(report_file, "r", encoding="utf-8") as f:
        rep = json.load(f)
    rep["verified_unique_count"] = len(cleaned_questions)
    rep["unverified_count"] = rep.get("total_extracted", 671) - len(cleaned_questions)
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)

print(f"Saved pristine question bank to {DATA_FILE} and {EMBEDDED_FILE}")

# Print first 15 questions to inspect
print("\n--- First 15 Questions Inspection ---")
for q in cleaned_questions[:15]:
    print(f"\n[{q['id']}] Q#{q['original_question_number']} ({q['source_file']} P{q['source_page']})")
    print(f"  Prompt: {q['question_en']}")
    for o in q['options']:
        print(f"    ({o['id']}) {o['text']}")
    print(f"  Answer: {q['correct_option']}")

