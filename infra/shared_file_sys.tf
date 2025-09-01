# # This won't work with LocalStack Community.
# # Untested with LocalStack Pro nor on AWS directly.
# # References:
# # https://github.com/hardikpatel29/terraform-lambda-efs-demo/tree/master
# # https://github.com/terraform-aws-modules/terraform-aws-lambda/tree/v7.2.2/examples/with-efs

resource "aws_security_group" "efs_access_sg" {
  name   = "${var.project}-${var.env}-${var.efs_access_security_group}"
  vpc_id = aws_vpc.dgtmon_vpc.id
  ingress {
    from_port   = 2049
    to_port     = 2049
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    description = "HTTPS for Endpoint Interface"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.10.0.0/20"]
    # cidr_blocks = ["0.0.0.0/0"] # TODO: set particular cidr block?
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

locals {
  az_names       = data.aws_availability_zones.azs.names
  public_sub_ids = aws_subnet.efs_public.*.id
}

# resource "aws_subnet" "efs_public" {
#   count                   = length(slice(local.az_names, 0, 2))
#   vpc_id                  = aws_vpc.dgtmon_vpc.id
#   availability_zone       = local.az_names[count.index]
#   cidr_block              = cidrsubnet(var.cidr_block, 4, count.index)
#   map_public_ip_on_launch = true
# }

resource "aws_subnet" "efs_public" {
  vpc_id     = aws_vpc.dgtmon_vpc.id
  cidr_block = "10.10.0.0/20"
}

resource "aws_default_subnet" "default_eu" {
  availability_zone = "eu-central-1a"
}

resource "aws_efs_mount_target" "efs_mount" {
  file_system_id = aws_efs_file_system.shared_file_sys.id
  subnet_id      = aws_default_subnet.default_eu.id
  # subnet_id      = aws_subnet.efs_public.id # private subnet, despite the name
  # security_groups = [aws_security_group.efs_access_sg.id]
}

resource "aws_efs_file_system" "shared_file_sys" {
  creation_token   = "${var.project}-${var.env}-${var.efs_creation_token}"
  performance_mode = "generalPurpose"
  throughput_mode  = "bursting"
  encrypted        = true
}

resource "aws_efs_access_point" "efs_access_point" {
  file_system_id = aws_efs_file_system.shared_file_sys.id
  posix_user {
    gid = 1000
    uid = 1000
  }
  root_directory {
    path = "/lambda"
    creation_info {
      owner_gid   = 1000
      owner_uid   = 1000
      permissions = "0777"
    }
  }
}

resource "aws_efs_file_system_policy" "policy" {
  file_system_id                     = aws_efs_file_system.shared_file_sys.id
  bypass_policy_lockout_safety_check = true
  policy                             = <<POLICY
{
    "Version": "2012-10-17",
    "Id": "ExamplePolicy01",
    "Statement": [
        {
            "Sid": "ExampleStatement01",
            "Effect": "Allow",
            "Principal": {
                "AWS": "*"
            },
            "Resource": "${aws_efs_file_system.shared_file_sys.arn}",
            "Action": [
                "elasticfilesystem:ClientMount",
                "elasticfilesystem:ClientWrite",
                "elasticfilesystem:ClientRootAccess"
            ],
            "Condition": {
                "Bool": {
                    "aws:SecureTransport": "true"
                }
            }
        }
    ]
}
POLICY
}

# TODO: narrow
data "aws_iam_policy" "lambda_execute" {
  arn = "arn:aws:iam::aws:policy/AWSLambdaExecute"
}

# TODO: narrow
data "aws_iam_policy" "lambda_vpc" {
  arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# TODO: narrow
data "aws_iam_policy" "efs_full_access" {
  arn = "arn:aws:iam::aws:policy/AmazonElasticFileSystemFullAccess"
}

resource "aws_iam_role_policy_attachment" "lambda_execute_policy" {
  role       = aws_iam_role.preparer_iam.name
  policy_arn = data.aws_iam_policy.lambda_execute.arn
}

resource "aws_iam_role_policy_attachment" "lambda_vpc_policy" {
  role       = aws_iam_role.preparer_iam.name
  policy_arn = data.aws_iam_policy.lambda_vpc.arn
}

resource "aws_iam_role_policy_attachment" "lambda_efs_full_policy" {
  role       = aws_iam_role.preparer_iam.name
  policy_arn = data.aws_iam_policy.efs_full_access.arn
}
