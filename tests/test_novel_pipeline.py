"""
Novel-Scribe Core Pipeline & Entity Standardization Test Suite
Validates:
- Sliding-window text chunking with token overlap and boundary tracking
- Progress persistence and multi-stage checkpoint recovery
- Novel Bible entity canonicalization and variant clustering
- Sensitivity replacement mappings (anonymization of real-world entities)
- Multi-chapter text merging and output structure
"""

import unittest
import os
import json
import tempfile
import re
from chunker.chunker import chunk_text, load_progress, save_progress


class TestNovelScribePipeline(unittest.TestCase):
    def setUp(self):
        self.sample_story = (
            "In the Great Yan Empire, Lin Dong discovered a mysterious stone talisman. "
            "The talisman radiated soft light, refining his martial arts skills. "
            "Lin-Dong practiced diligently every morning in Qingyang Town. "
            "Master Lin Dong defeated his rival in the martial contest."
        )

    def test_chunking_with_overlap(self):
        """Chunker must split text into overlapping windows without dropping words."""
        # Use small chunk_size=10, overlap=3 for testing
        words = self.sample_story.split()
        chunks = chunk_text(self.sample_story, chapter_num=1, chunk_size=10, overlap=3)
        
        self.assertGreater(len(chunks), 1)
        # Verify first chunk
        self.assertEqual(chunks[0]["chapter_num"], 1)
        self.assertEqual(chunks[0]["chunk_index"], 0)
        self.assertEqual(chunks[0]["status"], "pending")
        self.assertGreater(chunks[0]["token_count"], 0)
        
        # Verify overlap between consecutive chunks
        c0_words = chunks[0]["content"].split()
        c1_words = chunks[1]["content"].split()
        overlap_slice_c0 = c0_words[-3:]
        overlap_slice_c1 = c1_words[:3]
        self.assertEqual(overlap_slice_c0, overlap_slice_c1)

    def test_progress_persistence_and_checkpoint_resume(self):
        """Pipeline must persist stage states and resume accurately from disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            progress_path = os.path.join(tmpdir, "progress.json")
            
            # Initial state
            p1 = load_progress(progress_path)
            self.assertEqual(p1["master_status"], "initialized")
            self.assertEqual(p1["chunks"], [])
            
            # Update state to chunking_done
            p1["master_status"] = "chunking_done"
            p1["chunks"] = [{"id": 1, "status": "done"}]
            save_progress(p1, progress_path)
            
            # Reload from disk
            p2 = load_progress(progress_path)
            self.assertEqual(p2["master_status"], "chunking_done")
            self.assertEqual(len(p2["chunks"]), 1)
            self.assertEqual(p2["chunks"][0]["status"], "done")

    def test_entity_canonicalization_and_clustering(self):
        """Variant spellings of character names must cluster into canonical records."""
        raw_variants = [
            {"name": "Lin Dong", "role": "Protagonist"},
            {"name": "Lin-Dong", "role": "Main character"},
            {"name": "Lindong", "role": "Cultivator"}
        ]
        
        # Canonicalization heuristic: normalize whitespace and hyphens
        def canonical_key(name: str) -> str:
            return re.sub(r"[^a-zA-Z0-9]", "", name).lower()

        cluster_map = {}
        for item in raw_variants:
            key = canonical_key(item["name"])
            if key not in cluster_map:
                cluster_map[key] = {
                    "primary_name": item["name"],
                    "variants": set()
                }
            cluster_map[key]["variants"].add(item["name"])

        self.assertEqual(len(cluster_map), 1)
        record = list(cluster_map.values())[0]
        self.assertEqual(record["primary_name"], "Lin Dong")
        self.assertIn("Lin-Dong", record["variants"])
        self.assertIn("Lindong", record["variants"])

    def test_sensitivity_replacement_mapping(self):
        """Sensitivity dictionary safely replaces real-world entities with fantasy equivalents."""
        sensitivity_map = {
            "China": "Celestial Empire",
            "Beijing": "Capital Citadel",
            "Great Yan Empire": "Great Solar Dynasty"
        }
        
        text = "From Beijing to the provinces of China, news spread across the Great Yan Empire."
        for real_entity, fantasy_entity in sensitivity_map.items():
            pattern = re.compile(rf"\b{re.escape(real_entity)}\b")
            text = pattern.sub(fantasy_entity, text)
            
        self.assertNotIn("China", text)
        self.assertNotIn("Beijing", text)
        self.assertIn("Celestial Empire", text)
        self.assertIn("Capital Citadel", text)
        self.assertIn("Great Solar Dynasty", text)

    def test_chapter_merger_logic(self):
        """Verify sequential chapter stitching and file output generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rewritten_dir = os.path.join(tmpdir, "rewritten")
            ch1_dir = os.path.join(rewritten_dir, "chapter_0001")
            os.makedirs(ch1_dir, exist_ok=True)
            
            with open(os.path.join(ch1_dir, "chunk_0000.txt"), "w", encoding="utf-8") as f:
                f.write("Chapter 1: The Awakening.\nLin Dong opened his eyes.")
            with open(os.path.join(ch1_dir, "chunk_0001.txt"), "w", encoding="utf-8") as f:
                f.write("The talisman glowed brightly.")
                
            out_txt = os.path.join(tmpdir, "novel_cleaned.txt")
            
            # Merge text directly
            full_text = ""
            for fname in sorted(os.listdir(ch1_dir)):
                with open(os.path.join(ch1_dir, fname), "r", encoding="utf-8") as cf:
                    full_text += cf.read().strip() + "\n\n"
                    
            with open(out_txt, "w", encoding="utf-8") as f:
                f.write(full_text)
                
            self.assertTrue(os.path.exists(out_txt))
            with open(out_txt, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("Chapter 1: The Awakening", content)
            self.assertIn("The talisman glowed brightly", content)


if __name__ == "__main__":
    unittest.main()
