# ## Ref:
# ## https://oxla.io/learn-the-best-way-how-to-deploy-and-connect-to-a-bastion-host-in-aws-ec2-with-terraform/
# ## See also:
# ## https://towardsaws.com/creating-a-bastion-host-for-secure-access-to-your-aws-infrastructure-with-terraform-17ee287bb3d

# # resource "aws_vpc" "dgtmon_vpc" {
# #   cidr_block = var.cidr_block
# #   #   enable_dns_hostnames = true
# #   #   enable_dns_support   = true
# # }

# resource "aws_subnet" "bastion_public_subnet" {
#   vpc_id            = aws_vpc.dgtmon_vpc.id
#   cidr_block        = "10.10.127.0/24"
#   availability_zone = "eu-central-1a"
# }

# resource "aws_subnet" "bastion_private_subnet" {
#   vpc_id            = aws_vpc.dgtmon_vpc.id
#   cidr_block        = "10.10.128.0/24"
#   availability_zone = "eu-central-1a"
# }

# # 10.10.0.0 - 10.10.255.255 CIDR range

# resource "aws_route_table" "bastion_route_table" {
#   vpc_id = aws_vpc.dgtmon_vpc.id
#   route {
#     cidr_block = "0.0.0.0/0"
#     gateway_id = aws_internet_gateway.dgtmon_igw.id
#   }
# }

# resource "aws_route_table_association" "bastion_route_table_association" {
#   subnet_id      = aws_subnet.bastion_public_subnet.id
#   route_table_id = aws_route_table.bastion_route_table.id
# }

# resource "aws_route_table" "bastion_private_route_table" {
#   vpc_id = aws_vpc.dgtmon_vpc.id
# }

# resource "aws_route_table_association" "bastion_private_route_table_association" {
#   subnet_id      = aws_subnet.bastion_private_subnet.id
#   route_table_id = aws_route_table.bastion_private_route_table.id
# }

# resource "aws_security_group" "bastion_security_group" {
#   name        = "bastion_allow_public_traffic"
#   description = "Allow TLS inbound traffic"
#   vpc_id      = aws_vpc.dgtmon_vpc.id
#   ingress {
#     description      = "Public-Traffic-TLS"
#     from_port        = "443"
#     to_port          = "443"
#     protocol         = "tcp"
#     cidr_blocks      = ["0.0.0.0/0"]
#     ipv6_cidr_blocks = ["::/0"]
#   }
#   ingress {
#     description      = "Public-Traffic-TLS"
#     from_port        = "22"
#     to_port          = "22"
#     protocol         = "tcp"
#     cidr_blocks      = ["0.0.0.0/0"]
#     ipv6_cidr_blocks = ["::/0"]
#   }
#   ingress {
#     description      = "Public-Traffic-TLS"
#     from_port        = "80"
#     to_port          = "80"
#     protocol         = "tcp"
#     cidr_blocks      = ["0.0.0.0/0"]
#     ipv6_cidr_blocks = ["::/0"]
#   }
#   egress {
#     from_port        = 0
#     to_port          = 0
#     protocol         = "-1"
#     cidr_blocks      = ["0.0.0.0/0"]
#     ipv6_cidr_blocks = ["::/0"]
#   }
# }

# ## The private security group open only to the public security group.
# ## Take note of how I referenced the security group in the ingress
# resource "aws_security_group" "bastion_ec2_instance_security_group" {
#   name        = "ec2_instance_security_group"
#   description = "Allow TLS inbound traffic"
#   vpc_id      = aws_vpc.dgtmon_vpc.id
#   ingress {
#     description     = "Public-Traffic-TLS"
#     from_port       = "443"
#     to_port         = "443"
#     protocol        = "tcp"
#     security_groups = [aws_security_group.bastion_security_group.id]
#   }
#   ingress {
#     description     = "Public-Traffic-TLS"
#     from_port       = "22"
#     to_port         = "22"
#     protocol        = "tcp"
#     security_groups = [aws_security_group.bastion_security_group.id]
#   }
#   ingress {
#     description     = "Public-Traffic-TLS"
#     from_port       = "80"
#     to_port         = "80"
#     protocol        = "tcp"
#     security_groups = [aws_security_group.bastion_security_group.id]
#   }
#   egress {
#     from_port        = 0
#     to_port          = 0
#     protocol         = "-1"
#     cidr_blocks      = ["0.0.0.0/0"]
#     ipv6_cidr_blocks = ["::/0"]
#   }
# }

# ## Create the bastion host server and enable the public IP address.
# resource "aws_instance" "bastion_host" {
#   ami                                  = data.aws_ami.ubuntu.id
#   instance_type                        = "t3a.micro"
#   availability_zone                    = "eu-central-1a"
#   instance_initiated_shutdown_behavior = "terminate"
#   key_name                             = aws_key_pair.bastion_keypair.id
#   subnet_id                            = aws_subnet.bastion_public_subnet.id
#   tenancy                              = "default"
#   ebs_optimized                        = false
#   associate_public_ip_address          = true
#   iam_instance_profile                 = aws_iam_instance_profile.bastion_instance_profile.id
#   ebs_block_device {
#     device_name           = "/dev/sda1"
#     volume_size           = 20
#     delete_on_termination = true
#     volume_type           = "gp2"
#   }
#   vpc_security_group_ids = [aws_security_group.bastion_ec2_instance_security_group.id]

# }

# ## The AMI will be used to create the EC2 instance without you having to check from the console manually.
# data "aws_ami" "ubuntu" {
#   most_recent = true
#   filter {
#     name   = "description"
#     values = ["*Ubuntu*"]
#   }
#   filter {
#     name   = "root-device-name"
#     values = ["/dev/sda1"]
#   }
#   filter {
#     name   = "root-device-type"
#     values = ["ebs"]
#   }
#   filter {
#     name   = "virtualization-type"
#     values = ["hvm"]
#   }
#   owners = ["amazon"]
# }

# output "ec2_global_ips" {
#   value = ["${aws_instance.bastion_host.*.public_ip}"]
# }

# output "ami_ubuntu_name" {
#   value = data.aws_ami.ubuntu.name
# }

# resource "aws_key_pair" "bastion_keypair" {
#   key_name   = "bastion_keypair"
#   public_key = file("./id_ed25519_dgtmon_bastion.pub")
# }

# resource "aws_iam_role" "bastion_instance_role" {
#   name               = "bastion_role"
#   path               = "/"
#   assume_role_policy = data.aws_iam_policy_document.bastion_assume_role.json
# }

# resource "aws_iam_instance_profile" "bastion_instance_profile" {
#   name = "test_profile"
#   role = aws_iam_role.bastion_instance_role.name
# }

# data "aws_iam_policy_document" "bastion_assume_role" {
#   statement {
#     effect = "Allow"
#     principals {
#       type        = "Service"
#       identifiers = ["ec2.amazonaws.com"]
#     }
#     actions = ["sts:AssumeRole"]
#   }
# }
