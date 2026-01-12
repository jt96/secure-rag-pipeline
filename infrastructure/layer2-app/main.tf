resource "aws_instance" "rag_server" {
  ami           = "ami-0e2c8caa4b6378d8c" # Ubuntu 24.04 (us-east-1)
  instance_type = "t2.micro"
  key_name      = "devops-key"

  iam_instance_profile        = local.iam_profile
  subnet_id                   = local.public_subnet_id
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

output "server_public_ip" {
  value = aws_instance.rag_server.public_ip
}