import os
import pymupdf

QUESTIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'questions')

doc = pymupdf.open(os.path.join(QUESTIONS_DIR, 'qa.pdf'))
pages_with_text = []
for i, page in enumerate(doc):
    t = page.get_text()
    if len(t.strip()) > 0:
        pages_with_text.append((i, len(t.strip())))
print(f"Pages with text in qa.pdf: {len(pages_with_text)} out of {len(doc)}")
doc.close()

