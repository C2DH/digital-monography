# ## SQS (Lambda trigger)

# ## Lambda (builder)

# data "aws_iam_policy_document" "assume_builderv2_role" {
#   statement {
#     effect = "Allow"
#     principals {
#       type        = "Service"
#       identifiers = ["lambda.amazonaws.com"]
#     }
#     actions = ["sts:AssumeRole"]
#   }
# }

# resource "aws_iam_role" "builderv2_iam" {
#   # name               = "builderv2_iam"
#   name               = "${var.project}-${var.env}-${var.role_builderv2}"
#   assume_role_policy = data.aws_iam_policy_document.assume_builderv2_role.json
# }

# data "aws_iam_policy_document" "builderv2" {
#   statement {
#     sid       = "AllowS3Permissions"
#     effect    = "Allow"
#     resources = ["*"] # TODO: limit
#     actions = [
#       "s3:PutObject",
#       "s3:PutObjectAcl",
#       "s3:GetObject",
#       "s3:GetObjectAcl",
#     ]
#   }
#   statement {
#     sid       = "AllowInvokingLambdas"
#     effect    = "Allow"
#     resources = ["arn:aws:lambda:${var.region}:*:function:*"]
#     actions   = ["lambda:InvokeFunction"]
#   }
#   statement {
#     sid       = "AllowCreatingLogGroups"
#     effect    = "Allow"
#     resources = ["arn:aws:logs:${var.region}:*:*"]
#     actions   = ["logs:CreateLogGroup"]
#   }
#   statement {
#     sid       = "AllowWritingLogs"
#     effect    = "Allow"
#     resources = ["arn:aws:logs:${var.region}:*:log-group:*:*"]
#     actions = [
#       "logs:CreateLogStream",
#       "logs:PutLogEvents",
#     ]
#   }
#   statement {
#     sid    = "AllowWritingAuditEvents"
#     effect = "Allow"
#     resources = [
#       aws_dynamodb_table.alerts_tbl.arn,
#       aws_dynamodb_table.audit_tbl.arn
#     ]
#     actions = [
#       "dynamodb:PutItem",
#     ]
#   }
#   statement {
#     sid       = "AllowLambdaVPCNetworking"
#     effect    = "Allow"
#     resources = ["*"]
#     actions = [
#       "ec2:DescribeNetworkInterfaces",
#       "ec2:CreateNetworkInterface",
#       "ec2:DeleteNetworkInterface",
#       "ec2:DescribeInstances",
#       "ec2:AttachNetworkInterface"
#     ]
#   }
# }

# resource "aws_iam_policy" "builderv2" {
#   name   = "${var.project}-${var.env}-${var.policy_builderv2}"
#   policy = data.aws_iam_policy_document.builderv2.json
# }

# resource "aws_iam_role_policy_attachment" "builderv2" {
#   role       = aws_iam_role.builderv2_iam.name
#   policy_arn = aws_iam_policy.builderv2.arn
# }

# resource "aws_lambda_function" "builderv2_func" {
#   function_name = "${var.project}-${var.env}-${var.lambda_builderv2_func}"
#   package_type  = "Image"
#   image_uri     = "${aws_ecr_repository.builderv2_repo.repository_url}:${local.builderv2_tag}"
#   role          = aws_iam_role.builderv2_iam.arn
#   depends_on = [
#     data.aws_cloudwatch_log_group.general_purpose_logs,
#     aws_efs_mount_target.efs_mount
#   ]
#   architectures = ["x86_64"]
#   timeout       = 900
#   memory_size   = 1024
#   logging_config {
#     log_group  = data.aws_cloudwatch_log_group.general_purpose_logs.name
#     log_format = "JSON"
#   }
#   file_system_config {
#     arn              = aws_efs_access_point.efs_access_point.arn
#     local_mount_path = "/mnt/efs"
#   }
#   vpc_config {
#     subnet_ids         = [aws_subnet.efs_public.id]
#     security_group_ids = [aws_security_group.efs_access_sg.id]
#   }
#   environment {
#     variables = {
#       STATICWS_WIP_BUCKET_NAME = aws_s3_bucket.staticws_wip.bucket
#     }
#   }
# }

# resource "aws_ecr_repository" "builderv2_repo" {
#   name                 = "${var.project}-dev-${var.microservice_builderv2}"
#   image_tag_mutability = "IMMUTABLE"
#   force_delete         = true
# }

# locals {
#   builderv2_tag = var.env == "main" ? local.versions_data.BUILDER_V2.STABLE : local.versions_data.BUILDER_V2.LATEST
# }
