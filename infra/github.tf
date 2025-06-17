## Archive S3 (TODO: after replacing with SQS, remove S3)

# resource "aws_s3_bucket" "archive_apkg_all" {
#   bucket = var.archive_apkg_all_bucket_name
#   lifecycle {
#     prevent_destroy = false
#   }
# }

# resource "aws_s3_bucket_versioning" "archive_apkg_all" {
#   bucket = aws_s3_bucket.archive_apkg_all.id
#   versioning_configuration {
#     status = "Enabled"
#   }
# }

# resource "aws_s3_bucket_object_lock_configuration" "archive_apkg_all" {
#   bucket              = aws_s3_bucket.archive_apkg_all.id
#   depends_on          = [aws_s3_bucket_versioning.archive_apkg_all]
#   object_lock_enabled = "Enabled"
# }

# # TODO: archive upload bucket, remove this one
# resource "aws_s3_bucket_lifecycle_configuration" "archive_apkg_all" {
#   bucket     = aws_s3_bucket.archive_apkg_all.id
#   depends_on = [aws_s3_bucket_versioning.archive_apkg_all]
#   rule {
#     id     = "archive_apkg_all_old_versions_to_archive"
#     status = "Enabled"
#     noncurrent_version_transition {
#       noncurrent_days = 30
#       storage_class   = "STANDARD_IA"
#     }
#     noncurrent_version_transition {
#       noncurrent_days = 60
#       storage_class   = "GLACIER"
#     }
#   }
# }

# data "aws_iam_policy_document" "archive_apkg_all_policy" {
#   statement {
#     actions = [
#       "s3:*" # TODO: limit
#     ]
#     resources = [
#       "arn:aws:s3:::${aws_s3_bucket.archive_apkg_all.bucket}",
#       "arn:aws:s3:::${aws_s3_bucket.archive_apkg_all.bucket}/*"
#     ]
#     principals {
#       type        = "AWS"
#       identifiers = [aws_iam_user.apkg_uploader.arn]
#     }
#   }
# }

# resource "aws_s3_bucket_policy" "archive_apkg_all_policy" {
#   bucket = aws_s3_bucket.archive_apkg_all.id
#   policy = data.aws_iam_policy_document.archive_apkg_all_policy.json
# }

## SQS (Lambda trigger)

resource "aws_sqs_queue" "pre_github_queue" {
  # name                        = "${var.sqs_github_trigger}.fifo"
  name                        = "${var.project}-${var.env}-${var.sqs_github_trigger}"
  fifo_queue                  = true
  receive_wait_time_seconds   = 15
  delay_seconds               = 5
  content_based_deduplication = true
  max_message_size            = 1024  # 1 KiB
  message_retention_seconds   = 86400 # 24 hours
  visibility_timeout_seconds  = 900
}

resource "aws_lambda_event_source_mapping" "pre_github" {
  event_source_arn = aws_sqs_queue.pre_github_queue.arn
  function_name    = aws_lambda_function.github_func.arn
  batch_size       = 1
}

## Lambda (github)

data "aws_iam_policy_document" "assume_github_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "github_iam" {
  # name               = "github_iam"
  name               = "${var.project}-${var.env}-${var.role_github}"
  assume_role_policy = data.aws_iam_policy_document.assume_github_role.json
}

data "aws_iam_policy_document" "github" {
  statement {
    sid       = "AllowS3Permissions"
    effect    = "Allow"
    resources = ["*"] # TODO: limit
    actions = [
      "s3:PutObject",
      "s3:PutObjectAcl",
      "s3:GetObject",
      "s3:GetObjectAcl",
    ]
  }
  # is this necessary?
  # statement {
  #   sid       = "AllowInvokingLambdas"
  #   effect    = "Allow"
  #   resources = ["arn:aws:lambda:${var.region}:*:function:*"]
  #   actions   = ["lambda:InvokeFunction"]
  # }
  statement {
    sid       = "AllowReceivingSQSMessages"
    effect    = "Allow"
    resources = [aws_sqs_queue.pre_github_queue.arn]
    actions = [
      "sqs:DeleteMessage",
      "sqs:ReceiveMessage",
      "sqs:GetQueueAttributes",
      "sqs:GetQueueUrl"
    ]
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
    resources = ["arn:aws:logs:${var.region}:*:log-group:*:*"]
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
  }
  statement {
    sid       = "AllowWritingAuditEvents"
    effect    = "Allow"
    resources = [aws_dynamodb_table.audit_tbl.arn]
    actions = [
      "dynamodb:PutItem",
    ]
  }
  statement {
    sid       = "AllowSecretsFetching"
    effect    = "Allow"
    resources = [data.aws_secretsmanager_secret.github_api_token.arn]
    # resources = ["arn:aws:secretsmanager:${var.region}:*:secret:dgtmon-${var.environment}-github-api-secrets*"]
    actions = [
      "secretsmanager:DescribeSecret",
      "secretsmanager:GetResourcePolicy",
      "secretsmanager:GetSecretValue",
    ]
  }
}

resource "aws_iam_policy" "github" {
  # name   = "github_policy"
  name   = "${var.project}-${var.env}-${var.policy_github}"
  policy = data.aws_iam_policy_document.github.json
}

resource "aws_iam_role_policy_attachment" "github" {
  role       = aws_iam_role.github_iam.name
  policy_arn = aws_iam_policy.github.arn
}

# resource "aws_lambda_permission" "allow_archive_apkg_all_to_invoke_lambda" {
#   statement_id  = "AllowExecutionFromS3Bucket"
#   action        = "lambda:InvokeFunction"
#   function_name = aws_lambda_function.github_func.arn
#   principal     = "s3.amazonaws.com"
#   source_arn    = aws_s3_bucket.archive_apkg_all.arn
# }

resource "aws_lambda_function" "github_func" {
  # function_name = "github"
  function_name = "${var.project}-${var.env}-${var.lambda_github_func}"
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.github_repo.repository_url}:${local.github_tag}"
  role          = aws_iam_role.github_iam.arn
  depends_on = [
    data.aws_cloudwatch_log_group.general_purpose_logs,
  ]
  architectures = ["x86_64"]
  timeout       = 900
  memory_size   = 1024
  logging_config {
    log_group  = data.aws_cloudwatch_log_group.general_purpose_logs.name
    log_format = "JSON"
  }
  environment {
    variables = {
      DYNAMODB_AUDIT_TBL      = aws_dynamodb_table.audit_tbl.name
      DYNAMODB_ALERTS_TBL     = aws_dynamodb_table.alerts_tbl.name
      IR_APKG_MD_BUCKET_NAME  = aws_s3_bucket.ir_apkg_md.bucket
      APKG_UPLOAD_BUCKET_NAME = aws_s3_bucket.upload_apkg.bucket
      GITHUB_SECRET_ID        = data.aws_secretsmanager_secret.github_api_token.id
    }
  }
}

# resource "aws_s3_bucket_notification" "archive_apkg_all_notification" {
#   bucket = aws_s3_bucket.archive_apkg_all.id
#   lambda_function {
#     lambda_function_arn = aws_lambda_function.github_func.arn
#     events              = ["s3:ObjectCreated:*", "s3:ObjectRemoved:*"]
#   }
#   depends_on = [aws_lambda_permission.allow_archive_apkg_all_to_invoke_lambda]
# }

resource "aws_ecr_repository" "github_repo" {
  name                 = "${var.project}-dev-${var.microservice_github}"
  image_tag_mutability = "IMMUTABLE"
  force_delete         = true
}

locals {
  github_tag = var.env == "main" ? local.versions_data.GITHUB.STABLE : local.versions_data.GITHUB.LATEST
}
