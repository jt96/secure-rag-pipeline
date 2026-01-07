# Hybrid RAG Infrastructure

## Project Overview
A **Cost-Optimized** Retrieval-Augmented Generation (RAG) pipeline designed for efficient document querying. Unlike standard RAG implementations that rely entirely on paid APIs, this architecture uses **Local Embeddings** (HuggingFace) to eliminate external embedding API costs and latency.

The system integrates a **serverless vector database (Pinecone)** for scalable retrieval with a **cloud-based LLM (Gemini)** for generation. The application is served via a modern **Streamlit Web Interface**, demonstrating a **Hybrid AI Architecture** that balances local processing efficiency with cloud scalability.

## Architecture
* **Ingestion Engine:** Python + LangChain for PDF parsing and recursive chunking.
* **Vector Store:** Pinecone (Serverless Index) for semantic search.
* **Cognitive Layer:** Hybrid approach using Local Embeddings (CPU) + Google Gemini (LLM) for answer synthesis.
* **Infrastructure:** AWS EC2 (Compute), Custom VPC (Network), Terraform (IaC), Bash (Provisioning).
* **Containerization:** Docker Compose (Local Dev) / Native Systemd (Cloud - *Coming Soon*).

## Tech Stack
* **Language:** Python 3.11
* **Interface:** Streamlit
* **Infrastructure as Code:** Terraform
* **Cloud Provider:** AWS (EC2, VPC, Security Groups)
* **Containerization:** Docker & Docker Compose
* **Testing:** Pytest & Unittest.mock
* **Framework:** LangChain v0.3
* **Database:** Pinecone (Vector DB)
* **AI Models:** `all-MiniLM-L6-v2` (Local) + `gemini-2.5-flash` (Cloud)

## Project Structure
```text
hybrid-rag/
├── infrastructure/         # IaC Configuration
│   ├── main.tf             # Server & Provider config
│   ├── security.tf         # Security Groups
│   ├── vpc.tf              # Network (VPC, Subnets, IGW)
│   ├── install_app.sh      # User Data / Provisioning Script
│   └── .terraform.lock.hcl # Provider version lock
├── src/                    # Application Source Code
│   ├── __init__.py         # Package marker
│   ├── app.py              # Streamlit Interface
│   ├── ingest.py           # Data Processing Engine
│   ├── rag.py              # RAG Logic & Chain
│   └── state_manager.py    # State Persistence
├── tests/                  # Unit Tests
│   ├── test_ingest.py
│   ├── test_rag.py
│   └── test_state_manager.py
├── .github/workflows/      # CI/CD
│   └── ci.yml              # GitHub Actions Workflow
├── data/                   # PDF Storage (Mapped Volume)
├── .dockerignore
├── .gitignore
├── Dockerfile              # Container Definition
├── docker-compose.yml      # Orchestration
├── LICENSE
├── pytest.ini              # Test Configuration
├── requirements.txt        # Python Dependencies
├── run_app.bat             # Windows Quick Start
└── start.sh                # Utility Script
```

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
docker compose run hybrid-rag-app python src/ingest.py
```

**Option D: Windows Chat Only "One-Click"**
Simply double-click the `run_app.bat` file in the root directory.
* This automatically starts Docker, waits for initialization, and opens your default web browser to the chat interface.

---

## ☁️ Sprint 4: Native Cloud Deployment (AWS EC2)

This phase deploys the application directly onto an Ubuntu EC2 instance using Terraform for infrastructure and a Bash User Data script for provisioning.

### Infrastructure Architecture
* **Compute:** AWS EC2 (t2.micro) running Ubuntu 24.04.
* **Network:** Custom VPC, Public Subnet, Internet Gateway.
* **Security:** Security Group allowing SSH (22), HTTP (80), and Streamlit (8501).
* **Provisioning:** `cloud-init` (User Data) script installs Python, Git, and Pip automatically.

### 🚀 How to Deploy

**1. Provision Infrastructure**
Navigate to the infrastructure directory and apply the Terraform configuration:
```bash
cd infrastructure
terraform init
terraform plan
terraform apply
```

**2. SSH into the Server**
Use the `server_public_ip` output from Terraform:
```bash
ssh -i "devops-key.pem" ubuntu@<YOUR_PUBLIC_IP>
```

**3. Configure Secrets (Manual Step)**
For security, the automated script creates a placeholder `.env` file. You must update it with valid API keys:
```bash
# On the server
sudo chown ubuntu:ubuntu hybrid-rag-infrastructure/.env
nano hybrid-rag-infrastructure/.env
```
*Update `GOOGLE_API_KEY`, `PINECONE_API_KEY`, and `PINECONE_INDEX_NAME` with your actual values.*

**4. Launch the Application**
Navigate to the project root and start the Streamlit server:
```bash
cd hybrid-rag-infrastructure
source venv/bin/activate
PYTHONPATH=. streamlit run src/app.py --server.address 0.0.0.0
```

**5. Access the Interface**
Open your web browser and navigate to:
`http://<YOUR_PUBLIC_IP>:8501`

**6. Clean Up**
To avoid costs, destroy the infrastructure when finished:
```bash
terraform destroy
```

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
   # Windows: .\venv\Scripts\activate
   # Mac/Linux: source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run Tests:**
   ```bash
   pytest
   ```

3. **Run Ingestion:**
   ```bash
   # Run from root, pointing to the src file
   python src/ingest.py
   ```

4. **Run UI:**
   ```bash
   streamlit run src/app.py
   ```