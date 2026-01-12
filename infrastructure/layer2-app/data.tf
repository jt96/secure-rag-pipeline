data "terraform_remote_state" "layer1" {
  backend = "local"

  config = {
    path = "../layer1-foundation/terraform.tfstate"
  }
}

locals {
  vpc_id           = data.terraform_remote_state.layer1.outputs.vpc_id
  public_subnet_id = data.terraform_remote_state.layer1.outputs.public_subnet_id
  ecr_url          = data.terraform_remote_state.layer1.outputs.ecr_repository_url
  iam_profile      = data.terraform_remote_state.layer1.outputs.iam_instance_profile_name
}