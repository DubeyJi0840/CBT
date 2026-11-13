import os
import pymupdf
import hashlib

QUESTIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'questions')

def get_page_hash(page):
    pix = page.get_pixmap(dpi=72)
    return hashlib.md5(pix.tobytes()).hexdigest()

def compare():
    qa_path = os.path.join(QUESTIONS_DIR, 'qa.pdf')
    qa_doc = pymupdf.open(qa_path)
    print(f"qa.pdf has {len(qa_doc)} pages")
    
    qa_hashes = []
    for i in range(len(qa_doc)):
        h = get_page_hash(qa_doc[i])
        qa_hashes.append(h)
    
    sets = [
        'set =1.pdf', 'set -2.pdf', 'set -3.pdf', 'set -4.pdf', 'set -5.pdf',
        'set-6.pdf', 'set-7.pdf', 'set 8.pdf', 'set 9.pdf', 'set 10.pdf'
    ]
    
    total_set_pages = 0
    matched_pages = 0
    set_page_map = []
    
    for s in sets:
        path = os.path.join(QUESTIONS_DIR, s)
        doc = pymupdf.open(path)
        print(f"\n{s}: {len(doc)} pages")
        total_set_pages += len(doc)
        for pno in range(len(doc)):
            h = get_page_hash(doc[pno])
            match_qa = [idx for idx, qh in enumerate(qa_hashes) if qh == h]
            if match_qa:
                matched_pages += 1
                set_page_map.append((s, pno, match_qa[0]))
            else:
                print(f"  Page {pno} NOT matched in qa.pdf")
        doc.close()
        
    print(f"\nTotal set pages: {total_set_pages}, Matched with qa.pdf: {matched_pages}")
    print(f"qa.pdf pages: {len(qa_doc)}")
    
    # Are there any qa.pdf pages not in the sets?
    matched_qa_indices = set([m[2] for m in set_page_map])
    unmatched_qa = [i for i in range(len(qa_doc)) if i not in matched_qa_indices]
    print(f"qa.pdf pages not in any set: {unmatched_qa}")

if __name__ == '__main__':
    compare()

