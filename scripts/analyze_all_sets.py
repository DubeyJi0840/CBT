import os
import pymupdf

QUESTIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'questions')

def analyze():
    files = [f for f in os.listdir(QUESTIONS_DIR) if f.lower().endswith('.pdf')]
    files.sort()
    
    for filename in files:
        filepath = os.path.join(QUESTIONS_DIR, filename)
        doc = pymupdf.open(filepath)
        print(f"=== {filename} ===")
        print(f"  Pages: {len(doc)}")
        
        # Check text or images
        for pno in range(len(doc)):
            page = doc[pno]
            # Check image sizes
            imgs = page.get_images()
            print(f"  Page {pno}: rect={page.rect}, images={len(imgs)}")
        doc.close()

if __name__ == '__main__':
    analyze()

