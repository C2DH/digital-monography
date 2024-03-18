# # This won't work with LocalStack Community.
# # Untested with LocalStack Pro nor on AWS directly.
# # References:
# # https://github.com/hardikpatel29/terraform-lambda-efs-demo/tree/master
# # https://github.com/terraform-aws-modules/terraform-aws-lambda/tree/v7.2.2/examples/with-efs

# data "aws_availability_zones" "azs" {
#   state = "available"
# }

# locals {
#   az_names       = data.aws_availability_zones.azs.names
#   public_sub_ids = aws_subnet.efs_public.*.id
# }

# resource "aws_vpc" "efsvpc" {
#   cidr_block           = var.cidr_block
#   enable_dns_hostnames = true
#   enable_dns_support   = true
#   tags = {
#     Environment = var.environment
#     Team        = "Network"
#     Name        = "EFSVPC"
#   }
# }

# resource "aws_internet_gateway" "efs_igw" {
#   vpc_id = aws_vpc.efsvpc.id
#   tags = {
#     Environment = var.environment
#     Team        = "Network"
#     Name        = "EFSGW"
#   }
# }

# resource "aws_subnet" "efs_public" {
#   count                   = length(slice(local.az_names, 0, 2))
#   vpc_id                  = aws_vpc.efsvpc.id
#   availability_zone       = local.az_names[count.index]
#   cidr_block              = cidrsubnet(var.cidr_block, 4, count.index)
#   map_public_ip_on_launch = true
#   tags = {
#     Environment = var.environment
#     Team        = "Network"
#     Name        = "EFSPUBSUBNET"
#   }
# }

# resource "aws_route_table" "efs_publicrt" {
#   vpc_id = aws_vpc.efsvpc.id
#   route {
#     cidr_block = "0.0.0.0/0"
#     gateway_id = aws_internet_gateway.efs_igw.id
#   }
#   tags = {
#     Environment = var.environment
#     Team        = "Network"
#     Name        = "efs-public-subnet"
#   }
# }

# resource "aws_route_table_association" "efs_pub_subnet_association" {
#   count          = length(slice(local.az_names, 0, 2))
#   subnet_id      = aws_subnet.efs_public.*.id[count.index]
#   route_table_id = aws_route_table.efs_publicrt.id
# }

# #===========security group for efs==========

# resource "aws_security_group" "efs_access_sg" {
#   name        = "efs_access_sg"
#   description = "EFS Access Group"
#   vpc_id      = aws_vpc.efsvpc.id

#   ingress {
#     from_port   = 2049
#     to_port     = 2049
#     protocol    = "tcp"
#     cidr_blocks = ["0.0.0.0/0"]
#   }

#   egress {
#     from_port   = 0
#     to_port     = 0
#     protocol    = "-1"
#     cidr_blocks = ["0.0.0.0/0"]
#   }
# }
