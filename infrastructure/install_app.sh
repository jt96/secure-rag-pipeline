#!/bin/bash
set -e

# --- System Updates & Docker Installation ---
sudo apt-get update
sudo apt-get install -y docker.io unzip awscli jq

sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu

# --- Dynamic Environment Discovery ---
# Retrieve metadata securely using IMDSv2
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
REGION=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" -s http://169.254.169.254/latest/meta-data/placement/region)
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URL="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/hybrid-rag-app"

# --- Authentication ---
aws ecr get-login-password --region "$REGION" | sudo docker login --username AWS --password-stdin "$ECR_URL"

# --- Retrieve Configuration (SSM) ---
PINECONE_KEY=$(aws ssm get-parameter --name "/hybrid-rag/PINECONE_API_KEY" --with-decryption --query Parameter.Value --output text --region "$REGION")
GOOGLE_KEY=$(aws ssm get-parameter --name "/hybrid-rag/GOOGLE_API_KEY" --with-decryption --query Parameter.Value --output text --region "$REGION")
PINECONE_INDEX=$(aws ssm get-parameter --name "/hybrid-rag/PINECONE_INDEX_NAME" --query Parameter.Value --output text --region "$REGION")
LLM_MODEL=$(aws ssm get-parameter --name "/hybrid-rag/LLM_MODEL" --query Parameter.Value --output text --region "$REGION")

# --- Launch Container ---
sudo docker pull "$ECR_URL:latest"

sudo docker run -d \
  --name hybrid-rag-app \
  --restart always \
  -p 80:8501 \
  -e PINECONE_API_KEY="$PINECONE_KEY" \
  -e GOOGLE_API_KEY="$GOOGLE_KEY" \
  -e PINECONE_INDEX_NAME="$PINECONE_INDEX" \
  -e LLM_MODEL="$LLM_MODEL" \
  "$ECR_URL:latest"