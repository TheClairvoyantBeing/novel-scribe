import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

class NovelMerger:
    def __init__(self, console):
        self.console = console

    def merge_chapters(self, rewritten_dir, output_txt, output_pdf):
        """
        Merges rewritten chunks into chapters and generates final outputs.
        """
        chapter_dirs = sorted([d for d in os.listdir(rewritten_dir) if os.path.isdir(os.path.join(rewritten_dir, d))])
        
        full_text = ""
        pdf_elements = []
        styles = getSampleStyleSheet()
        
        for chapter_dir in chapter_dirs:
            chapter_num = int(chapter_dir.split("_")[-1])
            chapter_title = f"Chapter {chapter_num}"
            
            full_text += f"{chapter_title}\n\n"
            pdf_elements.append(Paragraph(chapter_title, styles['Heading1']))
            pdf_elements.append(Spacer(1, 12))
            
            chunk_files = sorted([f for f in os.listdir(os.path.join(rewritten_dir, chapter_dir)) if f.endswith(".txt")])
            
            # Simple merge for now. 
            # In a more advanced version, we'd use the 400-token overlap for smooth stitching.
            # Here we just concatenate chunks.
            for f in chunk_files:
                with open(os.path.join(rewritten_dir, chapter_dir, f), 'r', encoding='utf-8') as cf:
                    content = cf.read().strip()
                    full_text += content + "\n\n"
                    # For PDF, handle basic paragraph breaks
                    for para in content.split('\n'):
                        if para.strip():
                            pdf_elements.append(Paragraph(para.strip(), styles['Normal']))
                    pdf_elements.append(Spacer(1, 12))
            
            full_text += "\n---\n\n"
            
        # Write TXT
        with open(output_txt, 'w', encoding='utf-8') as f:
            f.write(full_text)
            
        # Write PDF
        doc = SimpleDocTemplate(output_pdf, pagesize=letter)
        doc.build(pdf_elements)
        
        return len(chapter_dirs)
