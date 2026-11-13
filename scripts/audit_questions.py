import json
import re

with open('data/questions.json', 'r', encoding='utf-8') as f:
    questions = json.load(f)

print(f"Total questions in bank: {len(questions)}")

flagged = []
for idx, q in enumerate(questions):
    issues = []
    qid = q['id']
    prompt_en = q.get('question_en', '')
    prompt = q.get('question', '')
    opts = {o['id']: o['text'].strip() for o in q.get('options', [])}
    
    # 1. Prompt issues
    if len(prompt_en.strip()) < 15:
        issues.append(f"Short prompt ({len(prompt_en)} chars): '{prompt_en}'")
    if re.search(r'[\u4e00-\u9fff]', prompt_en):
        issues.append("Contains Chinese characters")
    if re.search(r'\b(ef|uee|fohh|yahif|qRa|fhua|grhi)\b', prompt_en, re.I):
        issues.append("Contains pseudo-Hindi Latin noise")
    if prompt_en.startswith('(') or prompt_en.startswith('.') or prompt_en.startswith('-'):
        issues.append(f"Prompt starts with artifact: '{prompt_en[:15]}'")
        
    # 2. Option issues
    for let in ['A', 'B', 'C', 'D']:
        ot = opts.get(let, '')
        if len(ot) < 1:
            issues.append(f"Option {let} is empty")
        elif len(ot) < 2 and not ot.isdigit():
            issues.append(f"Option {let} too short: '{ot}'")
        if re.search(r'[\u4e00-\u9fff]', ot):
            issues.append(f"Chinese char in Option {let}: '{ot}'")
        if re.search(r'^\(?([A-Da-d])\)?[\.\:\-\s]+', ot):
            issues.append(f"Redundant prefix in Option {let}: '{ot[:10]}'")
        if re.search(r'\b[1-9]\d?\.[\s\S]{5,}', ot):
            issues.append(f"Leaked text in Option {let}: '{ot[:30]}'")
            
    if issues:
        flagged.append({
            'index': idx,
            'id': qid,
            'file': q['source_file'],
            'page': q['source_page'],
            'qnum': q['original_question_number'],
            'prompt': prompt_en[:60],
            'options': opts,
            'issues': issues
        })

print(f"Flagged questions count: {len(flagged)} / {len(questions)}")
print("\nSample flagged questions:")
for item in flagged[:30]:
    print(f"[{item['index']}] {item['id']} ({item['file']} P{item['page']} Q#{item['qnum']}):")
    print(f"   Prompt: {item['prompt']}")
    print(f"   Options: {item['options']}")
    print(f"   Issues: {item['issues']}")

