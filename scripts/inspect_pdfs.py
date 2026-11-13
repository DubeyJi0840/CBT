import os
import sys
import fitz  # PyMuPDF

QUESTIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'questions')

def inspect_all():
    print(f"Scanning directory: {QUESTIONS_DIR}")
    if not os.path.exists(QUESTIONS_DIR):
        print("Directory does not exist!")
        return

    files = [f for f in os.listdir(QUESTIONS_DIR) if f.lower().endswith('.pdf')]
    files.sort()
    print(f"Found {len(files)} PDF files:")

    total_pages_all = 0
    for filename in files:
        filepath = os.path.join(QUESTIONS_DIR, filename)
        filesize = os.path.getsize(filepath)
        try:
            doc = fitz.open(filepath)
            num_pages = len(doc)
            total_pages_all += num_pages
            
            # Sample text from first 2 pages and last page
            text_lens = []
            has_images = 0
            for i in range(min(5, num_pages)):
                page = doc[i]
                txt = page.get_text()
                text_lens.append(len(txt.strip()))
                if len(page.get_images()) > 0:
                    has_images += 1

            last_page_text = ""
            if num_pages > 0:
                last_page_text = doc[-1].get_text()[:400].replace('\n', ' ')

            first_page_sample = doc[0].get_text()[:300].replace('\n', ' ') if num_pages > 0 else ""

            print(f"\n--- {filename} ---")
            print(f"  Size: {filesize / (1024*1024):.2f} MB, Pages: {num_pages}")
            print(f"  Sample text lengths on first pages: {text_lens}")
            print(f"  First page sample: {first_page_sample[:150]}...")
            print(f"  Last page sample: {last_page_text[:150]}...")
            doc.close()
        except Exception as e:
            print(f"Error opening {filename}: {e}")

    print(f"\nTotal PDFs: {len(files)}, Total Pages: {total_pages_all}")

if __name__ == '__main__':
    inspect_all()

