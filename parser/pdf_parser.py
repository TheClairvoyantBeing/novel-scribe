import fitz  # PyMuPDF
import os
import re

def extract_pdf_chapters(pdf_path, output_dir):
    """
    Extracts text from a PDF and splits it into chapters based on heuristics.
    """
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
        
    # Heuristic for chapter detection
    # Looks for "Chapter X", "第X章", or "Chapter Name" patterns
    # This is a basic implementation; might need refinement based on actual samples.
    chapter_pattern = re.compile(r'(Chapter\s+\d+|第\d+章)', re.IGNORECASE)
    
    splits = chapter_pattern.split(full_text)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    chapter_count = 0
    # The first element might be front matter before the first chapter title
    if splits and not chapter_pattern.match(splits[0]):
        # Save as preface/prologue if significant
        if len(splits[0].strip()) > 100:
            chapter_count += 1
            with open(os.path.join(output_dir, f"chapter_{chapter_count:04d}_preface.txt"), 'w', encoding='utf-8') as f:
                f.write(splits[0].strip())
        splits = splits[1:]

    # Iterate through matches and their following text
    for i in range(0, len(splits), 2):
        if i + 1 < len(splits):
            title = splits[i].strip()
            content = splits[i+1].strip()
            
            chapter_count += 1
            chapter_filename = f"chapter_{chapter_count:04d}.txt"
            with open(os.path.join(output_dir, chapter_filename), 'w', encoding='utf-8') as f:
                f.write(f"{title}\n\n{content}")
                
    return chapter_count

if __name__ == "__main__":
    # Example usage
    # count = extract_pdf_chapters("sample.pdf", "chapters/raw")
    # print(f"Extracted {count} chapters.")
    pass
