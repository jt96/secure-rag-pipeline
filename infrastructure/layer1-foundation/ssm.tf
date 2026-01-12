resource "aws_ssm_parameter" "pinecone_api_key" {
  name        = "/hybrid-rag/PINECONE_API_KEY"
  description = "Pinecone API Key (Update manually in Console)"
  type        = "SecureString"
  value       = "CHANGE_ME"

  lifecycle {
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