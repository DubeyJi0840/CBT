import os
import pymupdf

QUESTIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'questions')
doc = pymupdf.open(os.path.join(QUESTIONS_DIR, 'set =1.pdf'))
page = doc[0]
pix = page.get_pixmap(dpi=150)
pix.save("temp_page0.png")
doc.close()
print("Saved temp_page0.png")

