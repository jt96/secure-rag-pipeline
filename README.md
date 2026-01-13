# Hybrid RAG Infrastructure

## Project Overview
A **Cloud-Native** Retrieval-Augmented Generation (RAG) pipeline deployed on AWS. This project moves beyond local tutorials to demonstrate a proper **Infrastructure-as-Code (IaC)** workflow.

The goal was to build a system that is cost-effective for a single developer but follows modern engineering practices:
* **Cost Optimized:** Custom Docker image reduced by **80%** (12GB -> 2.6GB) using CPU-only builds.
* **Automated:** The application server is stateless and provisions itself automatically using `user_data` scripts.
* **Observable:** Full integration with **AWS CloudWatch** for real-time logging without needing SSH.
* **Hybrid AI:** Combines **Local Embeddings** (HuggingFace) to save costs with **Cloud LLMs** (Gemini) for quality.

## Architecture
The infrastructure uses a **Decoupled Layer Strategy** to separate long-term networking from ephemeral application servers:

* **Layer 1 (Foundation):** The "Hardware." VPC, Public Subnets, Internet Gateway, ECR Repository, and IAM Roles. Managed via Terraform.
* **Layer 2 (Application):** The "Software." A disposable EC2 instance that pulls the latest Docker artifact from ECR on startup.
* **Data Plane:** Pinecone (Serverless Vector DB) for storage and retrieval.
* **Observability:** Application `stdout` is streamed directly to AWS CloudWatch Logs via the `awslogs` Docker driver.

## Tech Stack
* **Language:** Python 3.11
* **Interface:** Streamlit
* **Infrastructure as Code:** Terraform (Split State: Foundation vs. App)
* **Cloud:** AWS (EC2, VPC, ECR, IAM, CloudWatch)
* **Containerization:** Docker (Multi-stage builds)
* **AI Framework:** LangChain v0.3
* **Testing:** Pytest & Unittest.mock

## Project Structure
```text
hybrid-rag-infrastructure/
├── infrastructure/             # Decoupled IaC Configuration
│   ├── layer1-foundation/      # The "Permanent" Layer
│   │   ├── ecr.tf              # Container Registry
│   │   ├── iam.tf              # Roles & Policies
│   │   ├── outputs.tf          # Exports VPC_ID, Subnet_ID, etc.
│   │   ├── providers.tf        # AWS Provider Config
│   │   ├── ssm.tf              # Parameter Store
│   │   └── vpc.tf              # Network (VPC, Subnets, IGW)
│   └── layer2-app/             # The "Disposable" Layer
│       ├── data.tf             # Data source lookups
│       ├── install_app.sh      # Boot script (Docker Pull & Run)
│       ├── main.tf             # EC2 Instance resource
│       ├── providers.tf        # AWS Provider Config
│       └── security.tf         # Security Groups (Firewall)
├── src/                        # Application Source Code
│   ├── __init__.py
│   ├── app.py                  # Streamlit Interface w/ Logging
│   ├── ingest.py               # PDF Processing Engine
│   ├── rag.py                  # RAG Logic
│   └── state_manager.py        # Session State Handling
├── tests/                      # Unit Test Suite
│   ├── test_ingest.py
│   ├── test_rag.py
│   └── test_state_manager.py
├── Dockerfile                  # Optimized Multi-Stage Build
├── docker-compose.yml          # Local Development Orchestration
├── requirements.txt            # Python Dependencies
├── run_app.bat                 # Windows Quick Start
└── start.sh                    # Container Entrypoint
```

## Quick Start (Local)

### 1. Configuration
Create a `.env` file in the root directory:
```env
PINECONE_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
PINECONE_INDEX_NAME=hybrid-rag
LLM_MODEL=gemini-2.5-flash
```

### 2. Run with Docker Compose
```bash
# Chat Only
docker compose run --service-ports hybrid-rag-app

# Ingest New Data & Chat
docker compose run --service-ports -e RUN_INGEST=true hybrid-rag-app
```
*Access the UI at:* **http://localhost:8501**

### 3. Windows Chat Only "One-Click"
Simply double-click the `run_app.bat` file in the root directory.
* This automatically starts Docker, waits for initialization, and opens your default web browser to the chat interface.

---

## Cloud Deployment (AWS)

This project uses a **Containerized Workflow**. I do not edit code on the server. I build locally, push to ECR, and the server pulls the update.

### Prerequisites
* AWS CLI configured
* Terraform installed

### Phase 1: Build & Push Artifact
1. **Build the Image:**
   ```powershell
   docker build -t hybrid-rag-app:latest .
   ```
2. **Push to AWS ECR:**
   ```powershell
   # Login
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

   # Tag & Push
   docker tag hybrid-rag-app:latest <YOUR_ECR_REPO_URL>:latest
   docker push <YOUR_ECR_REPO_URL>:latest
   ```

### Phase 2: Provision Infrastructure

**1. Deploy Layer 1 (Foundation)**
Creates the VPC and ECR Repo. (Run this once).
```bash
cd infrastructure/layer1-foundation
terraform apply
```

**2. Deploy Layer 2 (Application)**
Launches the server. The `user_data` script will automatically pull your Docker image and start the app.
```bash
cd ../layer2-app
terraform apply
```

**3. Access the App**
* Get the IP from the Terraform output: `instance_public_ip`.
* Visit: `http://<PUBLIC_IP>:8501`.

### Phase 3: Observability
Logs are not stored on the server. View them in the **AWS CloudWatch Console**:
* **Log Group:** `/hybrid-rag-logs`
* **Stream:** `hybrid-rag-stream`

---

## Development Workflow (CI/CD Lite)

To deploy a code change (e.g., fixing a bug in `app.py`):

1. **Edit Code** locally.
2. **Build & Push** the new Docker image to ECR.
3. **Cycle Layer 2**:
   ```bash
   cd infrastructure/layer2-app
   terraform destroy -auto-approve
   terraform apply -auto-approve
   ```
   *This destroys the old server and spins up a fresh one with the new code in ~2 minutes.*

---

## Testing & Quality Assurance
* **Framework:** `pytest`
* **Coverage:** 15 Unit Tests (Ingestion, RAG, State Manager).
* **Isolation:** Fully mocked external services (Pinecone/Gemini) to allow offline testing.

```bash
pytest
```