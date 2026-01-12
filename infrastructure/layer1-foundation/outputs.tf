output "vpc_id" {
  description = "The ID of the VPC"
  value       = aws_vpc.rag_vpc.id
}

output "public_subnet_id" {
  description = "The ID of the public subnet"
  value       = aws_subnet.public_subnet.id
}

output "iam_instance_profile_name" {
  description = "The name of the IAM instance profile for EC2"
  value       = aws_iam_instance_profile.ec2_profile.name
}

output "ecr_repository_url" {
  description = "The URL of the ECR repository"
  value       = aws_ecr_repository.app_repo.repository_url
}