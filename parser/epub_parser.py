import os
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import re

def extract_epub_chapters(epub_path, output_dir):
    """
    Extracts chapters from an EPUB file and saves them as plaintext files.
    """
    chapters = []
    
    try:
        # 1. Primary Method: ebooklib
        book = epub.read_epub(epub_path)
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                chapters.append(item.get_content())
    except Exception as e:
        # 2. Fallback Method: zipfile (for malformed EPUBs or EbookLib failure)
        print(f"[!] EbookLib failed: {e}. Attempting robust fallback parsing...")
        import zipfile
        try:
            with zipfile.ZipFile(epub_path, 'r') as z:
                # Get all html/xhtml files
                file_list = [f for f in z.namelist() if f.lower().endswith(('.xhtml', '.html', '.htm'))]
                
                # Exclude known non-chapter files
                excluded = ['nav.xhtml', 'toc.xhtml', 'cover.xhtml', 'titlepage.xhtml']
                file_list = [f for f in file_list if not any(ex in f.lower() for ex in excluded)]
                
                # Sort files to maintain potential chapter order
                file_list.sort()
                
                for file_name in file_list:
                    chapters.append(z.read(file_name))
        except Exception as fallback_e:
            print(f"[!] Fallback also failed: {fallback_e}")
            return 0

    if not chapters:
        return 0
            
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    chapter_count = 0
    for i, content in enumerate(chapters):
        soup = BeautifulSoup(content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
            
        text = soup.get_text()
        
        # Basic cleaning
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        if len(text.strip()) < 100: # Skip very short snippets (likely nav or metadata)
            continue
            
        chapter_count += 1
        chapter_filename = f"chapter_{chapter_count:04d}.txt"
        with open(os.path.join(output_dir, chapter_filename), 'w', encoding='utf-8') as f:
            f.write(text)
            
    return chapter_count

if __name__ == "__main__":
    # Example usage (can be tested if an epub is provided)
    # count = extract_epub_chapters("sample.epub", "chapters/raw")
    # print(f"Extracted {count} chapters.")
    pass
