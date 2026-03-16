import os
import json
from utils.nvidia_client import NvidiaNIMClient

class NovelRewriter:
    def __init__(self, client: NvidiaNIMClient, bible, console):
        self.client = client
        self.bible = bible
        self.console = console

    def rewrite_chunk(self, chunk, model_standard="meta/llama-3.3-70b-instruct", model_long="deepseek-v3.1"):
        """
        Rewrites a chunk using the novel bible.
        """
        # Determine which model to use
        model = model_standard
        if chunk["token_count"] > 5000:
            model = model_long
            
        bible_context = json.dumps(self.bible, indent=2)
        
        prompt = f"""
        You are a professional novel editor. Your task is to rewrite the following chunk of a translated web novel to ensure consistency with the provided "Novel Bible".
        
        STRICT INSTRUCTIONS:
        1. Standardize character names, locations, and terms according to the Bible.
        2. DO NOT change the plot, events, dialogue meaning, or tone.
        3. Clean up awkward translation artifacts (e.g., rigid Chinese-to-English grammar).
        4. Do not add any new content or summary.
        5. Return ONLY the rewritten text.
        
        NOVEL BIBLE:
        {bible_context}
        
        CHUNK TEXT:
        {chunk['content']}
        """
        
        try:
            response = self.client.client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": "You are a professional editor."}, {"role": "user", "content": prompt}],
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            self.console.print(f"[red]Error rewriting chunk {chunk['chunk_index']}: {e}[/red]")
            return None
