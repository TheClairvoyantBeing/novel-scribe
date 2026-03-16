import os
import json
import re

# We'll use a simple word-based tokenization for now to avoid dependency issues if tiktoken isn't installed,
# but in a production environment, we'd use tiktoken or similar.
def count_tokens_approx(text):
    """Simple word-based token approximation."""
    return len(re.findall(r'\w+', text))

def chunk_text(text, chapter_num, chunk_size=4000, overlap=400):
    """
    Splits text into chunks of chunk_size with overlap.
    Returns a list of chunk dictionaries with metadata.
    """
    words = text.split()
    chunks = []
    start = 0
    chunk_index = 0
    
    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunk_text_content = " ".join(chunk_words)
        
        # Calculate character positions (approximate but consistent for merging)
        # Note: This is an approximation since we split by words. 
        # For precision, Stage 5 will use anchor-based matching as planned.
        
        chunk_data = {
            "chapter_num": chapter_num,
            "chunk_index": chunk_index,
            "token_count": count_tokens_approx(chunk_text_content),
            "content": chunk_text_content,
            "start_word_index": start,
            "end_word_index": min(end, len(words)),
            "status": "pending"
        }
        
        chunks.append(chunk_data)
        
        if end >= len(words):
            break
            
        start = end - overlap
        chunk_index += 1
        
    return chunks

def save_progress(progress_data, progress_file):
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress_data, f, indent=4)

def load_progress(progress_file):
    if os.path.exists(progress_file):
        with open(progress_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "master_status": "initialized",
        "chunks": [],
        "substitutions": []
    }

if __name__ == "__main__":
    # Example usage
    sample_text = "This is a sample text " * 1000
    chunks = chunk_text(sample_text, chapter_num=1)
    print(f"Created {len(chunks)} chunks.")
