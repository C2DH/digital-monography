# S3 for outputting verifier messages

resource "aws_s3_bucket" "verification_msg" {
  bucket        = var.verification_msgs_bucket_name
  force_destroy = true
}

resource "aws_s3_bucket_cors_configuration" "verification_msg_config" {
  bucket = aws_s3_bucket.verification_msg.id

  cors_rule {
    allowed_methods = ["HEAD", "GET"]
    allowed_origins = ["*"]
    max_age_seconds = 43200
  }
}

data "aws_iam_policy_document" "verification_msg_policy" {
  statement {
    actions = [
      "s3:*" # TODO: limit
    ]
    resources = [
      "arn:aws:s3:::${aws_s3_bucket.verification_msg.bucket}",
      "arn:aws:s3:::${aws_s3_bucket.verification_msg.bucket}/*"
    ]
    principals {
      type        = "AWS"
      identifiers = [aws_iam_user.apkg_uploader.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "verification_msg_policy" {
  bucket = aws_s3_bucket.verification_msg.id
  policy = data.aws_iam_policy_document.verification_msg_policy.json
}

## Lambda (verifier)

data "aws_iam_policy_document" "assume_verifier_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "verifier_iam" {
  name               = "verifier_iam"
  assume_role_policy = data.aws_iam_policy_document.assume_verifier_role.json
}

data "aws_iam_policy_document" "verifier" {
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
    sid    = "AllowWritingAuditEvents"
    effect = "Allow"
    resources = [
      aws_dynamodb_table.alerts_tbl.arn,
      aws_dynamodb_table.audit_tbl.arn
    ]
    actions = [
      "dynamodb:PutItem",
    ]
  }
  statement {
    sid    = "AllowReadAndWriteToDynamoDB"
    effect = "Allow"
    resources = [
      aws_dynamodb_table.warnings_tbl.arn,
    ]
    actions = [
      "dynamodb:PutItem",
    ]
  }
  statement {
    sid       = "AllowSendingSQSMessages"
    effect    = "Allow"
    resources = [aws_sqs_queue.pre_builder_queue.arn]
    actions = [
      "sqs:SendMessage",
      "sqs:GetQueueAttributes",
      "sqs:GetQueueUrl"
    ]
  }
  statement {
    sid       = "AllowLambdaVPCNetworking"
    effect    = "Allow"
    resources = ["*"]
    actions = [
      "ec2:DescribeNetworkInterfaces",
      "ec2:CreateNetworkInterface",
      "ec2:DeleteNetworkInterface",
      "ec2:DescribeInstances",
      "ec2:AttachNetworkInterface"
    ]
  }
}

resource "aws_iam_policy" "verifier" {
  name   = "verifier_policy"
  policy = data.aws_iam_policy_document.verifier.json
}

resource "aws_iam_role_policy_attachment" "verifier" {
  role       = aws_iam_role.verifier_iam.name
  policy_arn = aws_iam_policy.verifier.arn
}

resource "aws_lambda_permission" "allow_ir_apkg_html_to_invoke_lambda" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.verifier_func.arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.ir_apkg_html.arn
}

resource "aws_lambda_permission" "allow_verifier_access_s3_via_vpc_endpoint" {
  statement_id  = "AllowS3AccessViaVPCEndpoint"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.verifier_func.arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_vpc_endpoint.s3_endpoint.arn
}

resource "aws_lambda_function" "verifier_func" {
  function_name = "verifier"
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.verifier_repo.repository_url}:${local.verifier_stable_v}"
  role          = aws_iam_role.verifier_iam.arn
  depends_on = [
    data.aws_cloudwatch_log_group.general_purpose_logs,
    aws_efs_mount_target.efs_mount
  ]
  architectures = ["x86_64"]
  timeout       = 900
  memory_size   = 1024
  logging_config {
    log_group  = data.aws_cloudwatch_log_group.general_purpose_logs.name
    log_format = "JSON"
  }
  file_system_config {
    arn              = aws_efs_access_point.efs_access_point.arn
    local_mount_path = "/mnt/efs"
  }
  vpc_config {
    subnet_ids         = [aws_subnet.efs_public.id]
    security_group_ids = [aws_security_group.efs_access_sg.id]
  }
}

resource "aws_s3_bucket_notification" "ir_apkg_html_notification" {
  bucket = aws_s3_bucket.ir_apkg_html.id
  lambda_function {
    lambda_function_arn = aws_lambda_function.verifier_func.arn
    events              = ["s3:ObjectCreated:*", "s3:ObjectRemoved:*"]
  }
  depends_on = [aws_lambda_permission.allow_ir_apkg_html_to_invoke_lambda]
}

resource "aws_ecr_repository" "verifier_repo" {
  name                 = var.verifier_repo_name
  image_tag_mutability = "IMMUTABLE"
}

locals {
  verifier_stable_v = local.versions_data.VERIFIER_STABLE_V
}
