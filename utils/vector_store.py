import chromadb
from chromadb.utils import embedding_functions
import os
import json

import torch
class VectorStore:
    def __init__(self, db_path="output/chroma_db"):
        if not os.path.exists(db_path):
            os.makedirs(db_path)
            
        self.client = chromadb.PersistentClient(path=db_path)
        
        # Determine device for embeddings
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Use SentenceTransformerEmbeddingFunction for better GPU control
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2",
            device=device
        )
        
        self.collection = self.client.get_or_create_collection(
            name="novel_bible",
            embedding_function=self.ef
        )

    def upsert_bible_entry(self, entity_type, entity_name, description, metadata=None):
        """
        Add or update an entry in the vector store.
        """
        combined_text = f"{entity_type}: {entity_name}. {description}"
        doc_id = f"{entity_type}_{entity_name}".replace(" ", "_").lower()
        
        self.collection.upsert(
            documents=[combined_text],
            metadatas=[metadata or {"type": entity_type, "name": entity_name}],
            ids=[doc_id]
        )

    def query_context(self, text, n_results=5):
        """
        Retrieve relevant context for a given text chunk.
        """
        results = self.collection.query(
            query_texts=[text],
            n_results=n_results
        )
        return results["documents"][0] if results["documents"] else []

    def clear(self):
        """
        Clear the collection.
        """
        self.client.delete_collection("novel_bible")
        self.collection = self.client.create_collection(
            name="novel_bible",
            embedding_function=self.ef
        )

    def search_keywords(self, text):
        """
        Simple keyword search for entities mentioned in the text.
        Returns a list of matching documents.
        """
        # Get all documents in the collection
        all_docs = self.collection.get()
        matches = []
        
        text_lower = text.lower()
        for i, doc in enumerate(all_docs["documents"]):
            metadata = all_docs["metadatas"][i]
            # Match by name or term
            name = metadata.get("name", "").lower()
            if name and name in text_lower:
                matches.append(doc)
                
        return list(set(matches))

    def import_from_json(self, bible_json_path):
        """
        Import an existing novel_bible.json into the vector store.
        """
        if not os.path.exists(bible_json_path):
            return
            
        with open(bible_json_path, 'r', encoding='utf-8') as f:
            bible = json.load(f)
            
        for category, entities in bible.items():
            if isinstance(entities, list):
                for entity in entities:
                    if isinstance(entity, dict):
                        name = entity.get("name") or entity.get("term") or str(entity)
                        desc = entity.get("description") or entity.get("meaning") or ""
                        self.upsert_bible_entry(category, name, desc)
                    else:
                        self.upsert_bible_entry(category, str(entity), "")
