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

resource "aws_vpc_endpoint" "s3_endpoint" {
  vpc_id          = aws_vpc.dgtmon_vpc.id
  service_name    = "com.amazonaws.${var.region}.s3"
  route_table_ids = [aws_route_table.vpc_to_s3_connectivity.id]
}

resource "aws_vpc_endpoint" "sqs_endpoint" {
  vpc_id          = aws_vpc.dgtmon_vpc.id
  service_name    = "com.amazonaws.${var.region}.sqs"
  route_table_ids = [aws_route_table.vpc_to_s3_connectivity.id]
}

resource "aws_route_table" "vpc_to_s3_connectivity" {
  vpc_id = aws_vpc.dgtmon_vpc.id
}

resource "aws_route_table_association" "a" {
  subnet_id      = aws_subnet.efs_public.id
  route_table_id = aws_route_table.vpc_to_s3_connectivity.id
}
