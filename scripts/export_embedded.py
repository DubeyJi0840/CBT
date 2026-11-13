import json
import os

root = os.path.dirname(os.path.dirname(__file__))
data_file = os.path.join(root, 'data', 'questions.json')
embedded_file = os.path.join(root, 'js', 'embedded-questions.js')

with open(data_file, 'r', encoding='utf-8') as f:
    questions = json.load(f)

with open(embedded_file, 'w', encoding='utf-8') as f:
    f.write('// Auto-generated embedded questions bank for offline file:// execution\n')
    f.write('window.EMBEDDED_QUESTIONS = ')
    json.dump(questions, f, ensure_ascii=False)
    f.write(';\n')

print(f"Successfully exported {len(questions)} verified questions to {embedded_file}")

