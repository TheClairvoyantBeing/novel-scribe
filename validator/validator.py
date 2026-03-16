import os
from gliner import GLiNER
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

class NovelValidator:
    def __init__(self, bible, console):
        self.bible = bible
        self.console = console
        # Load a small GLiNER model for entity detection
        self.model = GLiNER.from_pretrained("urchade/gliner_base_news-v2.1")
        self.labels = ["person", "location", "organization"]

    def validate_chapter(self, chapter_text, chapter_num):
        """
        Extracts entities from a chapter and cross-references with the bible.
        """
        entities = self.model.predict_entities(chapter_text, self.labels)
        
        bible_entities = set()
        for char in self.bible.get("characters", []):
            bible_entities.add(char["canonical"].lower())
            for v in char.get("variants", []):
                bible_entities.add(v.lower())
        
        # Add locations, sects etc.
        for loc in self.bible.get("locations", []): bible_entities.add(loc.lower())
        for sect in self.bible.get("sects", []): bible_entities.add(sect.lower())
        
        flags = []
        for ent in entities:
            ent_text = ent["text"].lower()
            if ent_text not in bible_entities:
                flags.append({
                    "text": ent["text"],
                    "label": ent["label"],
                    "start": ent["start"],
                    "end": ent["end"]
                })
                
        return flags

    def run_validation(self, rewritten_dir, output_file):
        """
        Runs validation over all rewritten chapters.
        """
        report = []
        chapter_dirs = sorted([d for d in os.listdir(rewritten_dir) if os.path.isdir(os.path.join(rewritten_dir, d))])
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        ) as p:
            task = p.add_task("Validating chapters...", total=len(chapter_dirs))
            
            for chapter_dir in chapter_dirs:
                chapter_num = int(chapter_dir.split("_")[-1])
                full_chapter_text = ""
                
                # Merge chunks for validation
                chunk_files = sorted([f for f in os.listdir(os.path.join(rewritten_dir, chapter_dir)) if f.endswith(".txt")])
                for f in chunk_files:
                    with open(os.path.join(rewritten_dir, chapter_dir, f), 'r', encoding='utf-8') as cf:
                        full_chapter_text += cf.read() + " "
                
                flags = self.validate_chapter(full_chapter_text, chapter_num)
                if flags:
                    report.append(f"Chapter {chapter_num}:")
                    for flag in flags:
                        report.append(f"  - Flagged: {flag['text']} ({flag['label']})")
                
                p.update(task, advance=1)
                
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(report))
            
        return len(report)
