import typer
import os
import json
import re
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.console import Console
from dotenv import load_dotenv

from parser.epub_parser import extract_epub_chapters
from parser.pdf_parser import extract_pdf_chapters
from chunker.chunker import chunk_text, load_progress, save_progress
from utils.nvidia_client import NvidiaNIMClient
from bible.extractor import BibleExtractor
from bible.clusterer import BibleClusterer
from rewriter.rewriter import NovelRewriter
from validator.validator import NovelValidator
from merger.merger import NovelMerger
from utils.vector_store import VectorStore

app = typer.Typer()
console = Console()
load_dotenv()

@app.command()
def process(
    input_file: str = typer.Option(..., "--input", "-i", help="Path to the .epub or .pdf novel file"),
    output_dir: str = typer.Option("output", "--output", "-o", help="Directory for output files"),
    chunk_size: int = typer.Option(4000, help="Chunk size in tokens"),
    overlap: int = typer.Option(400, help="Overlap size in tokens"),
    neutralize: bool = typer.Option(True, "--neutralize", help="Enable anonymization of real-world references"),
    workers: int = typer.Option(5, "--workers", "-w", help="Number of parallel workers for LLM tasks")
):
    """
    Standardize a novel by fixing naming and phrasing inconsistencies.
    """
    progress_file = os.path.join(output_dir, "progress.json")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    progress = load_progress(progress_file)
    
    # Stage 0: Ingestion
    if progress["master_status"] == "initialized":
        console.print("[bold blue]Stage 0: Ingestion & Parsing[/bold blue]")
        raw_dir = os.path.join(output_dir, "chapters", "raw")
        
        if input_file.endswith(".epub"):
            count = extract_epub_chapters(input_file, raw_dir)
        elif input_file.endswith(".pdf"):
            count = extract_pdf_chapters(input_file, raw_dir)
        else:
            console.print("[red]Error: Unsupported file format. Use .epub or .pdf.[/red]")
            return
            
        console.print(f"Extracted {count} chapters to {raw_dir}")
        progress["master_status"] = "ingestion_done"
        save_progress(progress, progress_file)

    # Stage 1: Chunking
    if progress["master_status"] == "ingestion_done":
        console.print("[bold blue]Stage 1: Chunking[/bold blue]")
        raw_dir = os.path.join(output_dir, "chapters", "raw")
        all_chunks = []
        
        chapter_files = sorted([f for f in os.listdir(raw_dir) if f.endswith(".txt")])
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as p:
            task = p.add_task("Chunking chapters...", total=len(chapter_files))
            
            for filename in chapter_files:
                chapter_path = os.path.join(raw_dir, filename)
                chapter_num = int(re.search(r'(\d+)', filename).group(1))
                
                with open(chapter_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                chunks = chunk_text(content, chapter_num, chunk_size, overlap)
                all_chunks.extend(chunks)
                p.update(task, advance=1)
                
        progress["chunks"] = all_chunks
        progress["master_status"] = "chunking_done"
        save_progress(progress, progress_file)
        console.print(f"Created {len(all_chunks)} chunks total.")

    # Stage 2: Novel Bible Generation
    if progress["master_status"] == "chunking_done":
        console.print("[bold blue]Stage 2: Novel Bible Generation[/bold blue]")
        client = NvidiaNIMClient()
        extractor = BibleExtractor(client, console)
        clusterer = BibleClusterer(client)
        
        raw_bible_data = extractor.extract_all_chunks(progress["chunks"])
        bible = clusterer.consolidate_bible(raw_bible_data)
        
        bible_path = os.path.join(output_dir, "novel_bible.json")
        with open(bible_path, 'w', encoding='utf-8') as f:
            json.dump(bible, f, indent=4)
            
        # Initialize Vector Store and Upsert
        console.print("[dim]Updating Vector Database...[/dim]")
        db_path = os.path.join(output_dir, "chroma_db")
        vs = VectorStore(db_path)
        vs.import_from_json(bible_path)
            
        progress["master_status"] = "bible_generated"
        save_progress(progress, progress_file)
        console.print(f"Bible generated and saved to {bible_path}")
        console.print("[yellow]MANDATORY: Please review novel_bible.json and run 'python main.py confirm-bible' when ready.[/yellow]")

    # Stage 3: Rewrite Pass
    if progress["master_status"] == "bible_confirmed":
        console.print("[bold blue]Stage 3: Rewrite Pass[/bold blue]")
        bible_path = os.path.join(output_dir, "novel_bible.json")
        with open(bible_path, 'r', encoding='utf-8') as f:
            bible = json.load(f)
            
        client = NvidiaNIMClient()
        db_path = os.path.join(output_dir, "chroma_db")
        vs = VectorStore(db_path)
        
        sensitivity_config = "utils/sensitivity_config.json" if neutralize else None
        rewriter = NovelRewriter(client, bible, console, vector_store=vs, sensitivity_config=sensitivity_config)
        rewritten_dir = os.path.join(output_dir, "chapters", "rewritten")
        if not os.path.exists(rewritten_dir):
            os.makedirs(rewritten_dir)
            
        from concurrent.futures import ThreadPoolExecutor

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as p:
            pending_chunks = [c for c in progress["chunks"] if c.get("status") == "pending"]
            task = p.add_task("Rewriting chunks...", total=len(progress["chunks"]))
            p.update(task, advance=len(progress["chunks"]) - len(pending_chunks))
            
            def process_rewrite(chunk):
                try:
                    rewritten_text = rewriter.rewrite_chunk(chunk)
                    if rewritten_text:
                        chapter_rewritten_dir = os.path.join(rewritten_dir, f"chapter_{chunk['chapter_num']:04d}")
                        os.makedirs(chapter_rewritten_dir, exist_ok=True)
                        
                        chunk_filename = f"chunk_{chunk['chunk_index']:04d}.txt"
                        with open(os.path.join(chapter_rewritten_dir, chunk_filename), 'w', encoding='utf-8') as f:
                            f.write(rewritten_text)
                        
                        chunk["status"] = "done"
                        # We don't save progress every single chunk in threads to avoid lock contention, 
                        # but we update the progress bar.
                        p.update(task, advance=1)
                        return True
                except Exception as e:
                    console.print(f"[red]Error in thread: {e}[/red]")
                p.update(task, advance=1)
                return False

            with ThreadPoolExecutor(max_workers=workers) as executor:
                list(executor.map(process_rewrite, pending_chunks))
            
            save_progress(progress, progress_file) # Final save for stage
                
        progress["master_status"] = "rewrite_complete"
        save_progress(progress, progress_file)
        console.print("Rewrite pass completed.")

    # Stage 4: Validation Pass
    if progress["master_status"] == "rewrite_complete":
        console.print("[bold blue]Stage 4: Validation Pass[/bold blue]")
        bible_path = os.path.join(output_dir, "novel_bible.json")
        with open(bible_path, 'r', encoding='utf-8') as f:
            bible = json.load(f)
            
        validator = NovelValidator(bible, console)
        rewritten_dir = os.path.join(output_dir, "chapters", "rewritten")
        validation_report = os.path.join(output_dir, "validation_report.txt")
        
        flag_count = validator.run_validation(rewritten_dir, validation_report)
        
        progress["master_status"] = "validation_done"
        save_progress(progress, progress_file)
        console.print(f"Validation completed. Generated report with {flag_count} flags at {validation_report}")

    # Stage 5: Merge & Output
    if progress["master_status"] == "validation_done":
        console.print("[bold blue]Stage 5: Merge & Output[/bold blue]")
        merger = NovelMerger(console)
        rewritten_dir = os.path.join(output_dir, "chapters", "rewritten")
        out_txt = os.path.join(output_dir, "novel_cleaned.txt")
        out_pdf = os.path.join(output_dir, "novel_cleaned.pdf")
        
        chapter_count = merger.merge_chapters(rewritten_dir, out_txt, out_pdf)
        
        progress["master_status"] = "output_generated"
        save_progress(progress, progress_file)
        console.print(f"Final outputs generated: {out_txt}, {out_pdf}")

    # Stage 6: Summary Report
    if progress["master_status"] == "output_generated":
        console.print("[bold blue]Stage 6: Summary Report[/bold blue]")
        summary = {
            "total_chapters": len(set([c["chapter_num"] for c in progress.get("chunks", [])])),
            "total_chunks": len(progress.get("chunks", [])),
            "status": "completed",
            "output_files": ["novel_cleaned.txt", "novel_cleaned.pdf"]
        }
        
        summary_path = os.path.join(output_dir, "summary.json")
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=4)
            
        progress["master_status"] = "complete"
        save_progress(progress, progress_file)
        console.print(f"Project completed. Summary saved to {summary_path}")

    console.print(f"\n[green]Current Status: {progress['master_status']}[/green]")

@app.command()
def confirm_bible(output_dir: str = typer.Option("output", "--output", "-o")):
    """Confirm the generated novel bible to proceed to rewrite pass."""
    progress_file = os.path.join(output_dir, "progress.json")
    progress = load_progress(progress_file)
    if progress.get("master_status") != "bible_generated":
        console.print("[red]Error: Bible must be generated first.[/red]")
        return
        
    progress["master_status"] = "bible_confirmed"
    save_progress(progress, progress_file)
    console.print("[green]Bible confirmed. You can now run 'python main.py process' to start the rewrite pass.[/green]")

@app.command()
def status(output_dir: str = typer.Option("output", "--output", "-o")):
    """Show the current progress status."""
    progress_file = os.path.join(output_dir, "progress.json")
    if not os.path.exists(progress_file):
        console.print("[yellow]No project progress found in this directory.[/yellow]")
        return
    progress = load_progress(progress_file)
    console.print(f"Master Status: [bold]{progress.get('master_status', 'Not Started')}[/bold]")
    console.print(f"Total Chunks: {len(progress.get('chunks', []))}")

@app.command()
def env():
    """Setup the environment variables by copying .env.example to .env."""
    if os.path.exists(".env"):
        overwrite = typer.confirm(".env file already exists. Overwrite?")
        if not overwrite:
            return
            
    import shutil
    if os.path.exists(".env.example"):
        shutil.copy(".env.example", ".env")
        console.print("[green]Created .env from .env.example[/green]")
        
        api_key = typer.prompt("Enter your NVIDIA API Key (optional, press Enter to skip)", default="", show_default=False)
        if api_key:
            with open(".env", "r") as f:
                lines = f.readlines()
            with open(".env", "w") as f:
                for line in lines:
                    if line.strip().startswith("NVIDIA_API_KEY="):
                        f.write(f"NVIDIA_API_KEY={api_key}\n")
                    else:
                        f.write(line)
            console.print("[green]NVIDIA API Key updated in .env[/green]")
    else:
        console.print("[red]Error: .env.example not found. Please ensure it exists in the root directory.[/red]")

@app.command()
def reindex(output_dir: str = typer.Option("output", "--output", "-o")):
    """Rebuild the vector database from novel_bible.json."""
    bible_path = os.path.join(output_dir, "novel_bible.json")
    if not os.path.exists(bible_path):
        console.print(f"[red]Error: {bible_path} not found.[/red]")
        return
        
    db_path = os.path.join(output_dir, "chroma_db")
    vs = VectorStore(db_path)
    console.print(f"Reindexing Bible into {db_path}...")
    vs.clear()
    vs.import_from_json(bible_path)
    console.print("[green]Reindexing complete.[/green]")

if __name__ == "__main__":
    app()
