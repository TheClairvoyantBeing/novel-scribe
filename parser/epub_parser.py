import os
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import re

def extract_epub_chapters(epub_path, output_dir):
    """
    Extracts chapters from an EPUB file and saves them as plaintext files.
    """
    book = epub.read_epub(epub_path)
    chapters = []
    
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            chapters.append(item.get_content())
            
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
