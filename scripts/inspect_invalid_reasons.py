import json
from collections import Counter

with open('test_extracted.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

invalid = [q for q in data if not q['is_valid']]
valid = [q for q in data if q['is_valid']]

print(f"Total: {len(data)}, Valid: {len(valid)}, Invalid: {len(invalid)}")
reasons = Counter([q['issue'] for q in invalid])
print("\nInvalid breakdown:")
for r, count in reasons.most_common():
    print(f"  {r}: {count}")

print("\nSample valid questions (first 3):")
for q in valid[:3]:
    print(f"\nID: {q['id']}, Q{q['question_number']}: {q['question']}")
    print(f"  Options: {[o['id'] + ': ' + o['text'] for o in q['options']]}")
    print(f"  Correct: {q['correct_option']}")

print("\nSample invalid questions (first 3):")
for q in invalid[:3]:
    print(f"\nID: {q['id']}, Q{q['question_number']}: {q['question']}")
    print(f"  Issue: {q['issue']}")
    print(f"  Options found: {[o['id'] + ': ' + o['text'] for o in q['options']]}")

