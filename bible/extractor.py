import os
import json
from concurrent.futures import ThreadPoolExecutor
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from utils.nvidia_client import NvidiaNIMClient

class BibleExtractor:
    def __init__(self, client: NvidiaNIMClient, console):
        self.client = client
        self.console = console

    def extract_all_chunks(self, chunks, max_workers=5):
        """
        Extracts entities from all chunks using qwq-32b.
        """
        raw_bible_data = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        ) as p:
            task = p.add_task("Extracting entities (Bible Pass)...", total=len(chunks))
            
            def process_chunk(chunk):
                try:
                    res = self.client.extract_entities(chunk["content"])
                    p.update(task, advance=1)
                    return res
                except Exception as e:
                    self.console.print(f"[red]Error extracting from chunk {chunk['chunk_index']}: {e}[/red]")
                    p.update(task, advance=1)
                    return None

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                results = list(executor.map(process_chunk, chunks))
                
            raw_bible_data = [r for r in results if r]
            
        return raw_bible_data
