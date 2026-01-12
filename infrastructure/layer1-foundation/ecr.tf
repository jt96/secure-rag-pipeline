resource "aws_ecr_repository" "app_repo" {
  name                 = "hybrid-rag-app"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Project = "Hybrid-RAG"
  }
}
