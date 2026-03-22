import os
import json
from utils.nvidia_client import NvidiaNIMClient

class NovelRewriter:
    def __init__(self, client: NvidiaNIMClient, bible, console, vector_store=None, sensitivity_config=None):
        self.client = client
        self.bible = bible
        self.console = console
        self.vector_store = vector_store
        
        # Load sensitivity config if provided
        if sensitivity_config:
            with open(sensitivity_config, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = {"neutralize_real_world_references": False, "mappings": {}}

    def search_keywords_local(self, text):
        """
        Scan the text for terms already in the Bible to ensure exact matches are picked up.
        """
        matches = []
        if not self.bible or not isinstance(self.bible, dict):
            return matches

        text_lower = text.lower()
        
        # Check Characters
        for char in self.bible.get("characters", []):
            name = char.get("canonical", "").lower()
            if name and name in text_lower:
                variants = ", ".join(char.get("variants", []))
                matches.append(f"Character: {char['canonical']} (Variants: {variants})")
        
        # Check Locations
        for loc in self.bible.get("locations", []):
            if loc.lower() in text_lower:
                matches.append(f"Location: {loc}")
                
        # Check Sects/Organizations
        for sect in self.bible.get("sects", []):
            if sect.lower() in text_lower:
                matches.append(f"Sect/Organization: {sect}")
                    
        return matches

    def rewrite_chunk(self, chunk, model_standard="meta/llama-3.3-70b-instruct", model_long="deepseek-v3.1"):
        """
        Rewrites a chunk using the novel bible and optional RAG context.
        """
        model = model_standard
        if chunk["token_count"] > 5000:
            model = model_long
            
        # Get context from Vector Store (Hybrid Search) if available
        rag_context = ""
        if self.vector_store:
            # 1. Vector Search
            vector_docs = self.vector_store.query_context(chunk['content'], n_results=3)
            # 2. Keyword Search (Exact matches for names in the bible)
            keyword_docs = self.search_keywords_local(chunk['content'])
            
            # Combine and deduplicate
            combined_docs = list(set(vector_docs + keyword_docs))
            
            if combined_docs:
                rag_context = "\nRELEVANT BIBLE CONTEXT (HYBRID RAG):\n" + "\n".join(combined_docs)
        
        # Fallback to full bible if RAG is not used or provides nothing
        bible_context = ""
        if not rag_context:
            bible_context = "NOVEL BIBLE:\n" + json.dumps(self.bible, indent=2)
            
        # Sensitivity instructions
        sensitivity_instr = ""
        if self.config.get("neutralize_real_world_references"):
            mappings = json.dumps(self.config.get("mappings", {}), indent=2)
            sensitivity_instr = f"""
            6. SENSITIVITY FILTER: Identify and anonymize real-world countries, cities, and historical figures. 
               Use the following mappings if found: {mappings}
               Otherwise, replace them with fictional-sounding names consistent with the novel's setting.
            """
        
        prompt = f"""
        You are a professional novel editor. Your task is to rewrite the following chunk of a translated web novel to ensure consistency with the provided "Novel Bible".
        
        STRICT INSTRUCTIONS:
        1. Standardize character names, locations, and terms according to the Bible.
        2. DO NOT change the plot, events, dialogue meaning, or tone.
        3. Clean up awkward translation artifacts (e.g., rigid Chinese-to-English grammar).
        4. Do not add any new content or summary.
        5. Return ONLY the rewritten text.
        {sensitivity_instr}
        
        {bible_context}
        {rag_context}
        
        CHUNK TEXT:
        {chunk['content']}
        """
        
        try:
            response = self.client.client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": "You are a professional editor specialized in web novel standardization."}, {"role": "user", "content": prompt}],
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            self.console.print(f"[red]Error rewriting chunk {chunk['chunk_index']}: {e}[/red]")
            return None
            response = self.client.client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": "You are a professional editor specialized in web novel standardization."}, {"role": "user", "content": prompt}],
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            self.console.print(f"[red]Error rewriting chunk {chunk['chunk_index']}: {e}[/red]")
            return None
