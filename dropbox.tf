## DynamoDB (cursors)

# resource "aws_dynamodb_table" "cursors_tbl" {
#   name         = var.dgtmon_dev_dyndb_cursors_tbl
#   hash_key     = "account"
#   billing_mode = "PAY_PER_REQUEST"

#   attribute {
#     name = "account"
#     type = "S"
#   }

#   ttl {
#     attribute_name = "expires_at"
#     enabled        = true
#   }
# }

## Lambda (dropbox)

data "aws_iam_policy_document" "assume_dropbox_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "dropbox_iam" {
  name               = "dropbox_iam"
  assume_role_policy = data.aws_iam_policy_document.assume_dropbox_role.json
}

data "aws_iam_policy_document" "dropbox" {
  statement {
    sid       = "AllowInvokingLambdas"
    effect    = "Allow"
    resources = ["arn:aws:lambda:${var.region}:*:function:*"]
    actions   = ["lambda:InvokeFunction"]
  }
  statement {
    sid       = "AllowCreatingLogGroups"
    effect    = "Allow"
    resources = ["arn:aws:logs:${var.region}:*:*"]
    actions   = ["logs:CreateLogGroup"]
  }
  statement {
    sid       = "AllowWritingLogs"
    effect    = "Allow"
    resources = ["arn:aws:logs:${var.region}:*:log-group:/aws/*:*"]
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
  }
  statement {
    sid       = "AllowSecretsFetching"
    effect    = "Allow"
    resources = ["arn:aws:secretsmanager:${var.region}:*:secret:dgtmon-${var.environment}-github-api-secrets*"]
    actions = [
      "secretsmanager:DescribeSecret",
      "secretsmanager:GetResourcePolicy",
      "secretsmanager:GetSecretValue",
    ]
  }
  statement {
    sid       = "AllowReadAndWriteToDynamoDB"
    effect    = "Allow"
    resources = [aws_dynamodb_table.tokens_tbl.arn, aws_dynamodb_table.cursors_tbl.arn]
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DeleteItem",
      "dynamodb:Scan",
      "dynamodb:Query"
    ]
  }
  statement {
    sid       = "AllowReceivingSQSMessages"
    effect    = "Allow"
    resources = [aws_sqs_queue.entrypoint_to_dropbox.arn]
    actions = [
      "sqs:DeleteMessage",
      "sqs:ReceiveMessage",
      "sqs:GetQueueAttributes",
      "sqs:GetQueueUrl"
    ]
  }
}

resource "aws_iam_policy" "dropbox" {
  name   = "dropbox_policy"
  policy = data.aws_iam_policy_document.dropbox.json
}

resource "aws_iam_role_policy_attachment" "dropbox" {
  role       = aws_iam_role.dropbox_iam.name
  policy_arn = aws_iam_policy.dropbox.arn
}

resource "aws_lambda_event_source_mapping" "pre_dropbox" {
  event_source_arn = aws_sqs_queue.entrypoint_to_dropbox.arn
  function_name    = aws_lambda_function.dropbox_func.arn
}

# resource "aws_lambda_permission" "allow_upload_apkg_to_invoke_lambda" {
#   statement_id  = "AllowExecutionFromS3Bucket"
#   action        = "lambda:InvokeFunction"
#   function_name = aws_lambda_function.dropbox_func.arn
#   principal     = "s3.amazonaws.com"
#   source_arn    = aws_s3_bucket.upload_apkg.arn
# }

# resource "aws_lambda_permission" "allow_dropbox_access_s3_via_vpc_endpoint" {
#   statement_id  = "AllowS3AccessViaVPCEndpoint"
#   action        = "lambda:InvokeFunction"
#   function_name = aws_lambda_function.dropbox_func.arn
#   principal     = "s3.amazonaws.com"
#   source_arn    = aws_vpc_endpoint.s3_endpoint.arn
# }

# resource "aws_lambda_permission" "allow_dropbox_access_sqs_via_vpc_endpoint" {
#   statement_id  = "AllowSQSAccessViaVPCEndpoint"
#   action        = "lambda:SendMessage"
#   function_name = aws_lambda_function.dropbox_func.arn
#   principal     = "sqs.amazonaws.com"
#   source_arn = aws_sqs_queue.pre_builder_queue.arn
# }

resource "aws_lambda_function" "dropbox_func" {
  function_name = "dropbox"
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.dropbox_repo.repository_url}:${local.dropbox_stable_v}"
  role          = aws_iam_role.dropbox_iam.arn
  depends_on = [
    data.aws_cloudwatch_log_group.general_purpose_logs,
    # aws_efs_mount_target.efs_mount
  ]
  architectures = ["x86_64"]
  timeout       = 900
  memory_size   = 1024
  logging_config {
    log_group  = data.aws_cloudwatch_log_group.general_purpose_logs.name
    log_format = "JSON"
  }
  #   file_system_config {
  #     arn              = aws_efs_access_point.efs_access_point.arn
  #     local_mount_path = "/mnt/efs"
  #   }
  #   vpc_config {
  #     subnet_ids         = [aws_subnet.efs_public.id]
  #     security_group_ids = [aws_security_group.efs_access_sg.id]
  #   }
}

# resource "aws_s3_bucket_notification" "upload_apkg_notification" {
#   bucket = aws_s3_bucket.upload_apkg.id
#   lambda_function {
#     lambda_function_arn = aws_lambda_function.dropbox_func.arn
#     events              = ["s3:ObjectCreated:*", "s3:ObjectRemoved:*"]
#   }
#   depends_on = [aws_lambda_permission.allow_upload_apkg_to_invoke_lambda]
# }

resource "aws_ecr_repository" "dropbox_repo" {
  name                 = var.dropbox_repo_name
  image_tag_mutability = "IMMUTABLE"
}

locals {
  dropbox_stable_v = local.versions_data.DROPBOX_STABLE_V
}
