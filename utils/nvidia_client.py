import os
import requests
import json
from openai import OpenAI

class NvidiaNIMClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=self.api_key
        )

    def extract_entities(self, text, model="qwq-32b"):
        """
        Uses qwq-32b to extract entities from a text chunk.
        """
        prompt = f"""
        You are a specialized entity extractor for Chinese-to-English translated web novels.
        Extract character names (and their spelling variants), place names, cultivation ranks, sect names, and honorifics.
        Return the result ONLY as a structured JSON object.
        
        Chunk text:
        {text}
        
        Format:
        {{
            "characters": [{{ "name": "...", "variants": ["...", "..."], "description": "..." }}],
            "locations": ["...", "..."],
            "ranks": ["...", "..."],
            "sects": ["...", "..."],
            "terms": ["...", "..."]
        }}
        """
        
        response = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=2048,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)

    def get_embeddings(self, texts, model="nvidia/bge-m3"):
        """
        Uses bge-m3 to get embeddings for a list of strings.
        """
        # This is an illustration; actual endpoint for bge-m3 on NIM might vary.
        # Often it's a dedicated embeddings endpoint.
        response = self.client.embeddings.create(
            input=texts,
            model=model
        )
        return [data.embedding for data in response.data]
