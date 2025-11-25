# SecureGov RAG Pipeline 

## Project Overview
A compliance-focused Retrieval-Augmented Generation (RAG) pipeline designed for regulated environments. This system enables secure document querying while strictly enforcing **Data Sovereignty**.

Unlike standard RAG implementations, this architecture uses **Local Embeddings** (HuggingFace) to ensure document text is never sent to external embedding APIs, maintaining a strict boundary for sensitive data.

## Architecture
* **Ingestion Engine:** Python + LangChain for PDF parsing and recursive chunking.
* **Vector Store:** Pinecone (Serverless Index) for semantic search.
* **Cognitive Layer:** Hybrid approach using Local Embeddings (CPU) + Google Gemini (LLM) for answer synthesis.
* **Infrastructure:** Fully containerized via Docker with volume mapping for dynamic data injection.

## Tech Stack
* **Language:** Python 3.11
* **Containerization:** Docker
* **Framework:** LangChain v0.3
* **Database:** Pinecone (Vector DB)
* **AI Models:** `all-MiniLM-L6-v2` (Local) + `gemini-2.0-flash` (Cloud)

## Quick Start (Docker)

### 1. Configuration
Create a `.env` file in the root directory with your API keys:
```env
PINECONE_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
PINECONE_INDEX_NAME=secure-rag
# Optional: Custom folder name (Defaults to "data")
# DATA_FOLDER=my_docs
```

### 2. Prepare Data
Create a folder named `data` in your project root and add your PDF files.

### 3. Build the Image
```bash
docker build -t rag-app .
```

### 4. Run the Application

**Option A: Chat Only (Default)**
If you have already ingested data, just run the chat interface:

*Windows (PowerShell):*
```powershell
docker run -it --env-file .env -v ${PWD}/data:/app/data rag-app
```

*Mac/Linux:*
```bash
docker run -it --env-file .env -v $(pwd)/data:/app/data rag-app
```

**Option B: Ingest & Chat (First Run)**
To process new PDFs before chatting, set the `RUN_INGEST` variable to true:

*Windows (PowerShell):*
```powershell
docker run -it --env-file .env -e RUN_INGEST=true -v ${PWD}/data:/app/data rag-app
```

---

## Advanced Configuration

### Custom Data Folder
If you want to name your local folder something else (e.g., `my_docs`), you must update **both** your `.env` file and the Docker command.

1. **Update .env:**
   ```env
   DATA_FOLDER=my_docs
   ```

2. **Update Docker Command:**
   You must map your local folder to the **same name** inside the container:
   ```powershell
   # Format: -v ${PWD}/[Local_Name]:/app/[Env_Var_Name]
   docker run -it --env-file .env -v ${PWD}/my_docs:/app/my_docs rag-app
   ```

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