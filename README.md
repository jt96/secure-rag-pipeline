# Hybrid RAG Infrastructure

## Project Overview
A **Cost-Optimized** Retrieval-Augmented Generation (RAG) pipeline designed for efficient document querying. Unlike standard RAG implementations that rely entirely on paid APIs, this architecture uses **Local Embeddings** (HuggingFace) to eliminate external embedding API costs and latency.

The system integrates a **serverless vector database (Pinecone)** for scalable retrieval with a **cloud-based LLM (Gemini)** for generation. The application is served via a modern **Streamlit Web Interface**, demonstrating a **Hybrid AI Architecture** that balances local processing efficiency with cloud scalability.

## Architecture
* **Ingestion Engine:** Python + LangChain for PDF parsing and recursive chunking.
* **Vector Store:** Pinecone (Serverless Index) for semantic search.
* **Cognitive Layer:** Hybrid approach using Local Embeddings (CPU) + Google Gemini (LLM) for answer synthesis.
* **Infrastructure:** Fully containerized via Docker Compose with dynamic volume mapping.

## Tech Stack
* **Language:** Python 3.11
* **Interface:** Streamlit
* **Containerization:** Docker & Docker Compose
* **Testing:** Pytest & Unittest.mock
* **Framework:** LangChain v0.3
* **Database:** Pinecone (Vector DB)
* **AI Models:** `all-MiniLM-L6-v2` (Local) + `gemini-2.5-flash` (Cloud)

## Quick Start

### 1. Configuration
Create a `.env` file in the root directory with your API keys:
```env
PINECONE_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
PINECONE_INDEX_NAME=hybrid-rag

# Optional: Select the AI Model version
# Defaults to "gemini-2.5-flash" if not set.
# Use this to switch versions if Google deprecates a free tier model (e.g., "gemini-3.0-flash").
LLM_MODEL=gemini-2.5-flash

# Optional: Custom folder name for source PDFs (Defaults to "data")
DATA_FOLDER=data
```

### 2. Prepare Data
Create a folder named `data` in the project root directory and add your PDF files.

### 3. Run the Application

Use `docker compose run` with the `--service-ports` flag to ensure the web interface is accessible.

**Option A: Chat Only (Standard)**
Use this command to launch the Hybrid RAG Agent interface.
```bash
docker compose run --service-ports hybrid-rag-app
```
*Access the UI at:* **http://localhost:8501**

**Option B: Ingest & Chat (First Run)**
To process new PDFs before starting the web server:
```bash
docker compose run --service-ports -e RUN_INGEST=true hybrid-rag-app
```
*The system will scan for new files, vectorize them, upload to Pinecone, and move the source files to `data/processed/` to prevent duplication.*

**Option C: Ingest Only (Utility Mode)**
If you just want to process data and exit (without starting the web server):
```bash
docker compose run hybrid-rag-app python ingest.py
```

**Option D: Windows Chat Only "One-Click"**
Simply double-click the `run_app.bat` file in the root directory.
* This automatically starts Docker, waits for initialization, and opens your default web browser to the chat interface.

---

## Testing & Quality Assurance
The project includes a comprehensive unit test suite ensuring reliability across the pipeline.
* **Framework:** `pytest` with `unittest.mock`
* **Coverage:** 15 Unit Tests covering Ingestion logic, State Management, and RAG initialization.
* **Strategy:** Full isolation using Mocks to simulate Pinecone, Google Gemini, and File System interactions without network calls.

**To Run Tests:**
```bash
# Requires local dev environment (see below)
pytest
```

---

## Advanced Configuration

### Custom Data Folder
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

2. **Run Tests:**
   ```bash
   pytest
   ```

3. **Run Ingestion:**
   ```bash
   python ingest.py
   ```

4. **Run UI:**
   ```bash
   streamlit run app.py
   ```