# novel-scribe 🖋️

**novel-scribe** is an advanced AI-powered tool designed to standardize and refine translated web novels. It automates the process of extracting chapters, generating a "Novel Bible" for consistency, and rewriting text to ensure uniform character names, locations, and phrasing.

## 🚀 Features

- **Multi-Format Ingestion**: Supports extraction of chapters from both `.epub` and `.pdf` files.
- **AI-Generated Novel Bible**: Automatically identifies and clusters characters, locations, and organizations using NVIDIA NIM models.
- **Context-Aware Rewriting**: Standardizes terminology across chapters using high-performance LLMs (Llama 3.3 70B & DeepSeek V3).
- **Automated Validation**: Uses Named Entity Recognition (GLiNER) to cross-reference rewritten text with the Novel Bible to find inconsistencies.
- **Consolidated Output**: Merges processed chapters into a clean, standardized `.txt` and `.pdf` file.

## 🛠️ Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/TheClairvoyantBeing/novel-scribe.git
   cd novel-scribe
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   Copy `.env.example` to `.env` and add your NVIDIA API Key.
   ```bash
   cp .env.example .env
   ```

## 📖 Usage

The tool operates in stages to ensure maximum accuracy:

### 1. Start Processing
Extract chapters and generate the initial Novel Bible:
```bash
python main.py process --input path/to/your/novel.epub
```

### 2. Confirm the Bible
Review the generated `output/novel_bible.json`. If it looks correct, confirm it to proceed:
```bash
python main.py confirm-bible
```

### 3. Complete the Rewrite
Run the process command again to perform the rewrite and validation:
```bash
python main.py process --input path/to/your/novel.epub
```

### 4. Check Status
You can check the progress of your project at any time:
```bash
python main.py status
```

## 🤖 Technology Stack

- **Extraction**: `EbookLib`, `PyMuPDF`, `BeautifulSoup`
- **AI Intelligence**: `NVIDIA NIM` (Llama 3.3 70B, DeepSeek V3)
- **Validation**: `GLiNER` (Named Entity Recognition)
- **CLI Interface**: `Typer`, `Rich`
- **Output**: `ReportLab` (PDF generation)

## 📄 License

Individual project. All rights reserved.