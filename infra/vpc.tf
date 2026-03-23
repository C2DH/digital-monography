# Terraform does not create this resource, but instead "adopts" it into 
# management. If no default VPC exists, Terraform creates a new default VPC.
# By default, terraform destroy does not delete the default VPC but does 
# remove the resource from Terraform state.
# See https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/default_vpc
resource "aws_default_vpc" "default" {}

data "aws_subnets" "default_vpc_subnets" {
  filter {
    name   = "vpc-id"
    values = [aws_default_vpc.default.id]
  }
}

data "aws_security_group" "default" {
  filter {
    name   = "group-name"
    values = ["default"]
  }

  filter {
    name   = "vpc-id"
    values = [aws_default_vpc.default.id]
  }
}
