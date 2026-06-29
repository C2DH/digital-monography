# data "aws_ami" "amazon_linux_2023" {
#   most_recent = true
#   owners      = ["amazon"]

#   filter {
#     name   = "name"
#     values = ["al2023-ami-2023.*-x86_64"]
#   }

#   filter {
#     name   = "architecture"
#     values = ["x86_64"]
#   }

#   filter {
#     name   = "root-device-type"
#     values = ["ebs"]
#   }

#   filter {
#     name   = "virtualization-type"
#     values = ["hvm"]
#   }
# }

# resource "aws_iam_role" "role_websvr" {
#   name = "${var.project}-${var.env}-${var.role_websvr}"
#   assume_role_policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Action = "sts:AssumeRole"
#         Effect = "Allow"
#         Principal = {
#           Service = "ec2.amazonaws.com"
#         }
#       }
#     ]
#   })
# }

# resource "aws_iam_role_policy" "websvr_get_staticassets_policy" {
#   name = "${var.project}-${var.env}-${var.policy_websvr}"
#   role = aws_iam_role.role_websvr.id
#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Effect = "Allow"
#         Action = ["s3:GetObject"]
#         Resource = [
#           "${aws_s3_bucket.static_assets.arn}/*"
#         ]
#       },
#       {
#         Effect   = "Allow"
#         Action   = ["s3:ListBucket"]
#         Resource = [aws_s3_bucket.static_assets.arn]
#       }
#     ]
#   })
# }

# resource "aws_iam_role_policy_attachment" "websvr_ssm_core" {
#   role       = aws_iam_role.role_websvr.name
#   policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
# }

# resource "aws_iam_instance_profile" "websvr" {
#   name = var.websvr_profile_name
#   role = aws_iam_role.role_websvr.name
# }

# resource "aws_instance" "websvr" {
#   ami                    = data.aws_ami.amazon_linux_2023.id
#   instance_type          = "t3.micro"
#   subnet_id              = sort(data.aws_subnets.default_vpc_subnets.ids)[0]
#   vpc_security_group_ids = [data.aws_security_group.default.id]
#   iam_instance_profile   = aws_iam_instance_profile.websvr.name

#   user_data = <<-EOF
#     #!/bin/bash
#     set -e # stop execution immediately if any cmd fails
#     exec > >(tee /var/log/user-data.log) # log output to file
#     exec 2>&1 # stderr to stdout

#     yum update -y
#     yum install -y git
#     curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash
#     export NVM_DIR="$HOME/.nvm"
#     source $NVM_DIR/nvm.sh
#     echo "NVM version: $(nvm --version)"
#     nvm install 24.12.0
#     nvm use 24.12.0
#     npm install -g mystmd@1.8.0
#     echo "mystmd version: $(myst --version)"

#   EOF
# }
