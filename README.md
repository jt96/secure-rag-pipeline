# SecureGov RAG Pipeline

## Project Overview
A compliance-focused Retrieval-Augmented Generation (RAG) pipeline designed for regulated environments. This system enables secure document querying while strictly enforcing **Data Sovereignty**.

Unlike standard RAG implementations, this architecture uses **Local Embeddings** (HuggingFace) to ensure document text is never sent to external embedding APIs, maintaining a strict boundary for sensitive data.

## Architecture
* **Ingestion Engine:** Python + LangChain for PDF parsing and recursive chunking.
* **Vector Store:** Pinecone (Serverless Index) for semantic search.
* **Cognitive Layer:** Hybrid approach using Local Embeddings (CPU) + Google Gemini (LLM) for answer synthesis.
* **Infrastructure:** Fully containerized via Docker Compose with dynamic volume mapping.

## Tech Stack
* **Language:** Python 3.11
* **Containerization:** Docker & Docker Compose
* **Framework:** LangChain v0.3
* **Database:** Pinecone (Vector DB)
* **AI Models:** `all-MiniLM-L6-v2` (Local) + `gemini-2.0-flash` (Cloud)

## Quick Start

### 1. Configuration
Create a `.env` file in the root directory with your API keys:
```env
PINECONE_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
PINECONE_INDEX_NAME=secure-rag
# Optional: Custom folder name (Defaults to "data")
# DATA_FOLDER=data
```

### 2. Prepare Data
Create a folder named `data` in your project root directory and add your PDF files.

### 3. Run the Application

We use `docker compose run` to launch the interactive chat interface.

**Option A: Chat Only (Default)**
If you have already ingested data, run this command to start chatting immediately:
```bash
docker compose run rag-app
```

**Option B: Ingest & Chat (First Run)**
To process new PDFs before starting the chat, pass the ingestion environment variable:
```bash
docker compose run -e RUN_INGEST=true rag-app
```

---

## Custom Data Folder
If you change the `DATA_FOLDER` variable in your `.env` file (e.g., to `my_docs`), Docker Compose will automatically map that local folder to the container thanks to dynamic variable substitution in `docker-compose.yml`.

---

## Local Development (No Docker)

1. **Install Dependencies:**
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # Mac/Linux
   source venv/bin/activate
   
   pip install -r requirements.txt
   ```

2. **Run Ingestion:**
   ```bash
   python ingest.py
   ```

3. **Run Chat:**
   ```bash
   python rag.py
   ```