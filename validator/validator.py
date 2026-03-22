import torch
from gliner import GLiNER
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

class NovelValidator:
    def __init__(self, bible, console):
        self.bible = bible
        self.console = console
        # Detect GPU availability
        device = "cuda" if torch.cuda.is_available() else "cpu"
        # Load a small GLiNER model for entity detection
        self.model = GLiNER.from_pretrained("urchade/gliner_base_news-v2.1").to(device)
        self.labels = ["person", "location", "organization"]

    def validate_chapters_batch(self, chapter_texts, chapter_nums):
        """
        Extracts entities from a batch of chapters in one go.
        """
        # GLiNER can handle batching internally
        all_entities = self.model.predict_entities_batch(chapter_texts, self.labels)
        
        bible_entities = set()
        for char in self.bible.get("characters", []):
            bible_entities.add(char["canonical"].lower())
            for v in char.get("variants", []):
                bible_entities.add(v.lower())
        
        for loc in self.bible.get("locations", []): bible_entities.add(loc.lower())
        for sect in self.bible.get("sects", []): bible_entities.add(sect.lower())
        
        batch_results = []
        for i, entities in enumerate(all_entities):
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
            batch_results.append(flags)
            
        return batch_results

    def validate_chapter(self, chapter_text, chapter_num):
        """
        Extracts entities from a single chapter (legacy support).
        """
        return self.validate_chapters_batch([chapter_text], [chapter_num])[0]

    def run_validation(self, rewritten_dir, output_file):
        """
        Runs validation over all rewritten chapters.
        """
        report = []
        chapter_dirs = sorted([d for d in os.listdir(rewritten_dir) if os.path.isdir(os.path.join(rewritten_dir, d))])
        
        chapter_data = []
        for chapter_dir in chapter_dirs:
            chapter_num = int(chapter_dir.split("_")[-1])
            full_chapter_text = ""
            chunk_files = sorted([f for f in os.listdir(os.path.join(rewritten_dir, chapter_dir)) if f.endswith(".txt")])
            for f in chunk_files:
                with open(os.path.join(rewritten_dir, chapter_dir, f), 'r', encoding='utf-8') as cf:
                    full_chapter_text += cf.read() + " "
            chapter_data.append({"text": full_chapter_text, "num": chapter_num})

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        ) as p:
            task = p.add_task("Validating chapters...", total=len(chapter_data))
            
            # Batch size for validation
            batch_size = 8
            for i in range(0, len(chapter_data), batch_size):
                batch = chapter_data[i:i+batch_size]
                texts = [c["text"] for c in batch]
                nums = [c["num"] for c in batch]
                
                batch_flags = self.validate_chapters_batch(texts, nums)
                
                for k, flags in enumerate(batch_flags):
                    chapter_num = nums[k]
                    if flags:
                        report.append(f"Chapter {chapter_num}:")
                        for flag in flags:
                            report.append(f"  - Flagged: {flag['text']} ({flag['label']})")
                
                p.update(task, advance=len(batch))
                
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(report))
            
        return len(report)
