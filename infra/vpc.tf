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

# resource "aws_route_table" "efs_publicrt" {
#   vpc_id = aws_vpc.dgtmon_vpc.id
#   route {
#     cidr_block = "0.0.0.0/0"
#     gateway_id = aws_internet_gateway.dgtmon_igw.id
#   }
# }

# resource "aws_route_table_association" "efs_pub_subnet_association" {
#   count          = length(slice(local.az_names, 0, 2))
#   subnet_id      = aws_subnet.efs_public.*.id[count.index]
#   route_table_id = aws_route_table.efs_publicrt.id
# }
