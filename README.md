# novel-scribe 🖋️

**novel-scribe** is an advanced AI-powered tool designed to standardize and refine translated web novels. It automates the process of extracting chapters, generating a "Novel Bible" for consistency, and rewriting text to ensure uniform character names, locations, and phrasing.

## 🚀 Features

- **Multi-Format Ingestion**: Supports extraction of chapters from both `.epub` and `.pdf` files.
- **Massively Parallel Processing**: stage-based multithreaded rewriting for up to 10x faster completion.
- **Hybrid RAG (Vector + Keyword)**: Combines ChromaDB vector search with exact keyword matching for 100% terminology consistency.
- **AI-Generated Novel Bible**: Automatically identifies and clusters characters, locations, and organizations using NVIDIA NIM models.
- **GPU-Accelerated Validation**: Uses Named Entity Recognition (GLiNER) with CUDA batch-processing to find inconsistencies.
- **Anonymization Layer**: Automatically neutralizes real-world geographic and political references into fictional counterparts.

---

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/TheClairvoyantBeing/novel-scribe.git
   cd novel-scribe
   ```

2. **Quick Start (Windows)**:
   Run the automated setup script to create a virtual environment and install dependencies:
   ```bash
   ./setup.bat
   ```

3. **GPU Acceleration (Recommended)**:
   To leverage your NVIDIA GPU for entity recognition and embeddings:
   ```bash
   pip install torch --index-url https://download.pytorch.org/whl/cu126 --force-reinstall
   ```
   *(Note: Use `cu126` for Python 3.14 on Windows.)*

---

## 📖 Usage

### **1. Configure Environment**
```bash
python main.py env
```

### **2. Start Processing**
Extract chapters and generate the Novel Bible:
```bash
python main.py process --input path/to/your/novel.epub --workers 10 --neutralize
```
**Flags:**
- `--workers` / `-w`: Number of parallel LLM tasks (Default: 5).
- `--neutralize`: Enable fictionalization of real-world names.

### **3. Confirm & Rewrite**
Review `output/novel_bible.json`, then:
```bash
python main.py confirm-bible
python main.py process --input path/to/your/novel.epub --workers 10
```

---

## 🛠️ Tech Stack
- **Models**: NVIDIA NIM (Meta Llama 3.3 70B, DeepSeek V3).
- **Database**: ChromaDB (Vector Store).
- **NER**: GLiNER (Batch-optimized for GPU).
- **Parsing**: PyMuPDF, EbookLib.

---

## 📄 License
MIT License. Created for the web novel translation community.