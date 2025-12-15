@echo off
echo Starting Hybrid RAG...

:: Start Docker in detached mode (background)
docker compose up -d

:: Allow time for container initialization
timeout /t 5

:: Open UI
start http://localhost:8501

:: Stream logs
docker compose logs -f