# # This won't work with LocalStack Community.
# # Untested with LocalStack Pro nor on AWS directly.
# # References:
# # https://github.com/hardikpatel29/terraform-lambda-efs-demo/tree/master
# # https://github.com/terraform-aws-modules/terraform-aws-lambda/tree/v7.2.2/examples/with-efs

# resource "aws_efs_file_system" "efs_example" {
#   creation_token   = "efs-example"
#   performance_mode = "generalPurpose"
#   throughput_mode  = "bursting"
#   encrypted        = "true"
#   tags = {
#     Environment = var.environment
#     Team        = "Network"
#     Name        = "efsExample"
#   }
# }

# resource "aws_efs_mount_target" "efs_mount" {

#   count           = length(slice(local.az_names, 0, 2))
#   file_system_id  = aws_efs_file_system.efs_example.id
#   subnet_id       = aws_subnet.efs_public[count.index].id
#   security_groups = ["${aws_security_group.efs_access_sg.id}"]
# }

# resource "aws_efs_access_point" "efs_access_point" {
#   file_system_id = aws_efs_file_system.efs_example.id
#   posix_user {
#     gid = 1000
#     uid = 1000
#   }
#   root_directory {
#     path = "/access"
#     creation_info {
#       owner_gid   = 1000
#       owner_uid   = 1000
#       permissions = "777"
#     }
#   }
# }

# resource "aws_efs_file_system_policy" "policy" {
#   file_system_id                     = aws_efs_file_system.efs_example.id
#   bypass_policy_lockout_safety_check = true
#   policy                             = <<POLICY
# {
#     "Version": "2012-10-17",
#     "Id": "ExamplePolicy01",
#     "Statement": [
#         {
#             "Sid": "ExampleStatement01",
#             "Effect": "Allow",
#             "Principal": {
#                 "AWS": "*"
#             },
#             "Resource": "${aws_efs_file_system.efs_example.arn}",
#             "Action": [
#                 "elasticfilesystem:ClientMount",
#                 "elasticfilesystem:ClientWrite",
#                 "elasticfilesystem:ClientRootAccess"
#             ],
#             "Condition": {
#                 "Bool": {
#                     "aws:SecureTransport": "true"
#                 }
#             }
#         }
#     ]
# }
# POLICY
# }

# # TODO: narrow
# data "aws_iam_policy" "lambda_execute" {
#   arn = "arn:aws:iam::aws:policy/AWSLambdaExecute"
# }

# # TODO: narrow
# data "aws_iam_policy" "lambda_vpc" {
#   arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
# }

# # TODO: narrow
# data "aws_iam_policy" "efs_full_access" {
#   arn = "arn:aws:iam::aws:policy/AmazonElasticFileSystemFullAccess"
# }

# resource "aws_iam_role_policy_attachment" "lambda_execute_policy" {
#   role       = aws_iam_role.preparer_iam.name
#   policy_arn = data.aws_iam_policy.lambda_execute.arn
# }

# resource "aws_iam_role_policy_attachment" "lambda_vpc_policy" {
#   role       = aws_iam_role.preparer_iam.name
#   policy_arn = data.aws_iam_policy.lambda_vpc.arn
# }

# resource "aws_iam_role_policy_attachment" "lambda_efs_full_policy" {
#   role       = aws_iam_role.preparer_iam.name
#   policy_arn = data.aws_iam_policy.efs_full_access.arn
# }
