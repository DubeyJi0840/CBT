import json

with open('data/questions.json', 'r', encoding='utf-8') as f:
    questions = json.load(f)

with open('js/embedded-questions.js', 'w', encoding='utf-8') as f:
    f.write('// Auto-generated fallback for file:// protocol local execution without web server\n')
    f.write('window.EMBEDDED_QUESTIONS = ')
    json.dump(questions, f, ensure_ascii=False)
    f.write(';\n')

print(f"Generated js/embedded-questions.js with {len(questions)} questions.")

