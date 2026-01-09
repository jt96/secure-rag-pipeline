terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_instance" "rag_server" {
  ami           = "ami-0e2c8caa4b6378d8c" # Ubuntu 24.04 (us-east-1)
  instance_type = "t2.micro"
  key_name      = "devops-key"

  subnet_id                   = aws_subnet.public_subnet.id
  vpc_security_group_ids      = [aws_security_group.rag_sg.id]
  associate_public_ip_address = true

  # Bootstrapping script to install Python and the App
  user_data                   = file("install_app.sh")
  user_data_replace_on_change = true

  tags = {
    Name        = "dev-hybrid-rag-app-01"
    Environment = "Development"
    Project     = "Hybrid-RAG"
    ManagedBy   = "Terraform"
  }
}

# --- Secrets & Configuration (SSM Parameter Store) ---

resource "aws_ssm_parameter" "pinecone_api_key" {
  name        = "/hybrid-rag/PINECONE_API_KEY"
  description = "Pinecone API Key (Update manually in Console)"
  type        = "SecureString"
  value       = "CHANGE_ME"

  lifecycle {
    # Prevents Terraform from resetting the key after you manually update it
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "google_api_key" {
  name        = "/hybrid-rag/GOOGLE_API_KEY"
  description = "Google Gemini API Key (Update manually in Console)"
  type        = "SecureString"
  value       = "CHANGE_ME"

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "pinecone_index" {
  name        = "/hybrid-rag/PINECONE_INDEX_NAME"
  description = "Pinecone Index Name"
  type        = "String"
  value       = "hybrid-rag"
}

resource "aws_ssm_parameter" "llm_model" {
  name        = "/hybrid-rag/LLM_MODEL"
  description = "AI Model Version (e.g., gemini-2.5-flash)"
  type        = "String"
  value       = "gemini-2.5-flash"

  lifecycle {
    ignore_changes = [value]
  }
}

output "server_public_ip" {
  value = aws_instance.rag_server.public_ip
}