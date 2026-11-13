import os
import pymupdf

QUESTIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'questions')
sets = [
    'set =1.pdf', 'set -2.pdf', 'set -3.pdf', 'set -4.pdf', 'set -5.pdf',
    'set-6.pdf', 'set-7.pdf', 'set 8.pdf', 'set 9.pdf', 'set 10.pdf'
]

os.makedirs('key_images', exist_ok=True)
for i, s in enumerate(sets, 1):
    doc = pymupdf.open(os.path.join(QUESTIONS_DIR, s))
    last_page = doc[-1]
    pix = last_page.get_pixmap(dpi=150)
    out_path = f"key_images/set_{i}_key.png"
    pix.save(out_path)
    print(f"Saved Set {i} key image to {out_path} (from page {len(doc)-1} of {s})")
    doc.close()

