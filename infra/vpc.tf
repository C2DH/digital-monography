# This won't work with LocalStack Community.
# Untested with LocalStack Pro nor on AWS directly.
# References:
# https://github.com/hardikpatel29/terraform-lambda-efs-demo/tree/master
# https://github.com/terraform-aws-modules/terraform-aws-lambda/tree/v7.2.2/examples/with-efs

data "aws_availability_zones" "azs" {
  state = "available"
}

resource "aws_vpc" "dgtmon_vpc" {
  cidr_block           = var.cidr_block
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = {
    Name = "DIGITAL_MONOGRAPHY_PLATFORM_VPC"
  }
}

resource "aws_security_group" "efs_access_sg" {
  name   = "efs_access_sg"
  vpc_id = aws_vpc.dgtmon_vpc.id
  ingress {
    from_port   = 2049
    to_port     = 2049
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_subnet" "efs_public" {
  vpc_id     = aws_vpc.dgtmon_vpc.id
  cidr_block = "10.10.0.0/20"
}

resource "aws_vpc_endpoint" "s3_endpoint" {
  vpc_id          = aws_vpc.dgtmon_vpc.id
  service_name    = "com.amazonaws.${var.region}.s3"
  route_table_ids = [aws_route_table.vpc_to_s3_connectivity.id]
}

resource "aws_route_table" "vpc_to_s3_connectivity" {
  vpc_id = aws_vpc.dgtmon_vpc.id
  # route {
  #   cidr_block = "0.0.0.0/0"
  #   gateway_id = aws_internet_gateway.dgtmon_igw.id
  # }
}

resource "aws_route_table_association" "rt_main_subnet_association" {
  subnet_id      = aws_subnet.efs_public.id
  route_table_id = aws_route_table.vpc_to_s3_connectivity.id
}

# locals {
#   az_names       = data.aws_availability_zones.azs.names
#   public_sub_ids = aws_subnet.processor_subnet.*.id
# }

# resource "aws_subnet" "processor_subnet" {
#   count                   = length(slice(local.az_names, 0, 2))
#   vpc_id                  = aws_vpc.dgtmon_vpc.id
#   availability_zone       = local.az_names[count.index]
#   cidr_block              = cidrsubnet(var.cidr_block, 4, count.index)
#   map_public_ip_on_launch = true
# }

# resource "aws_internet_gateway" "dgtmon_igw" {
#   vpc_id = aws_vpc.dgtmon_vpc.id
# }
