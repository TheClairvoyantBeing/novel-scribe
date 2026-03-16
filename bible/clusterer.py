import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity
from utils.nvidia_client import NvidiaNIMClient

class BibleClusterer:
    def __init__(self, client: NvidiaNIMClient):
        self.client = client

    def cluster_names(self, names, threshold=0.15):
        """
        Clusters a list of names/variants based on bge-m3 embeddings.
        Threshold: distance threshold for AgglomerativeClustering (cosine distance).
        """
        if not names:
            return {}

        embeddings = self.client.get_embeddings(names)
        embeddings = np.array(embeddings)
        
        # AgglomerativeClustering with cosine affinity
        clustering = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=threshold,
            metric='cosine',
            linkage='average'
        )
        
        labels = clustering.fit_predict(embeddings)
        
        clusters = {}
        for idx, label in enumerate(labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(names[idx])
            
        return clusters

    def consolidate_bible(self, raw_bible_data):
        """
        Consolidates raw extraction data into a merged bible.
        """
        # Collect all character names and variants
        all_chars = []
        for chunk_res in raw_bible_data:
            for char in chunk_res.get("characters", []):
                all_chars.append(char["name"])
                all_chars.extend(char.get("variants", []))
        
        # Deduplicate
        all_chars = list(set(all_chars))
        
        # Cluster
        clusters = self.cluster_names(all_chars)
        
        consolidated_chars = []
        for label, variants in clusters.items():
            # Pick the longest name as the potential canonical form (often the most complete)
            canonical = max(variants, key=len)
            consolidated_chars.append({
                "canonical": canonical,
                "variants": sorted(list(set(variants)))
            })
            
        return {
            "characters": consolidated_chars,
            # Other fields (locations, sects etc.) would be similar
            "locations": list(set([l for r in raw_bible_data for l in r.get("locations", [])])),
            "ranks": list(set([rk for r in raw_bible_data for rk in r.get("ranks", [])])),
            "sects": list(set([s for r in raw_bible_data for s in r.get("sects", [])]))
        }
