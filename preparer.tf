# Intermediate MD S3

resource "aws_s3_bucket" "ir_apkg_md" {
  bucket        = var.ir_apkg_md_bucket_name
  force_destroy = true
}

data "aws_iam_policy_document" "ir_apkg_policy" {
  statement {
    actions = [
      "s3:*" # TODO: limit
    ]
    resources = [
      "arn:aws:s3:::${aws_s3_bucket.ir_apkg_md.bucket}",
      "arn:aws:s3:::${aws_s3_bucket.ir_apkg_md.bucket}/*"
    ]
    principals {
      type        = "AWS"
      identifiers = [aws_iam_user.ir_apkg_md_uploader.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "ir_apkg_policy" {
  bucket = aws_s3_bucket.ir_apkg_md.id
  policy = data.aws_iam_policy_document.ir_apkg_policy.json
}

# Uploader

resource "aws_iam_user" "ir_apkg_md_uploader" {
  name = "ir-apkg-md-uploader"
}

resource "aws_iam_access_key" "ir_apkg_md_uploader" {
  user = aws_iam_user.ir_apkg_md_uploader.name
}

output "ir_apkg_md_uploader_id" {
  value = aws_iam_access_key.ir_apkg_md_uploader.id
}

## Lambda (preparer)

data "aws_iam_policy_document" "assume_preparer_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "preparer_iam" {
  name               = "preparer_iam"
  assume_role_policy = data.aws_iam_policy_document.assume_preparer_role.json
}

data "aws_iam_policy_document" "preparer" {
  statement {
    sid       = "AllowS3Permissions"
    effect    = "Allow"
    resources = ["*"] # TODO: limit (since we also want to list buckets, include both "arn:aws:s3:::mybucket/*" and "arn:aws:s3:::mybucket")
    actions = [
      "s3:PutObject",
      "s3:PutObjectAcl",
      "s3:GetObject",
      "s3:GetObjectAcl",
      "s3:ListBucket"
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

resource "aws_iam_policy" "preparer" {
  name   = "preparer_policy"
  policy = data.aws_iam_policy_document.preparer.json
}

resource "aws_iam_role_policy_attachment" "preparer" {
  role       = aws_iam_role.preparer_iam.name
  policy_arn = aws_iam_policy.preparer.arn
}

resource "aws_lambda_permission" "allow_upload_apkg_to_invoke_lambda" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.preparer_func.arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.upload_apkg.arn
}

resource "aws_lambda_permission" "allow_preparer_access_s3_via_vpc_endpoint" {
  statement_id  = "AllowS3AccessViaVPCEndpoint"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.preparer_func.arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_vpc_endpoint.s3_endpoint.arn
}

resource "aws_lambda_permission" "allow_preparer_access_sqs_via_vpc_endpoint" {
  statement_id  = "AllowSQSAccessViaVPCEndpoint"
  action        = "lambda:SendMessage"
  function_name = aws_lambda_function.preparer_func.arn
  principal     = "sqs.amazonaws.com"
  # source_arn    = aws_vpc_endpoint.sqs_endpoint.arn
  source_arn = aws_sqs_queue.pre_builder_queue.arn
}

resource "aws_lambda_function" "preparer_func" {
  function_name = "preparer"
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.preparer_repo.repository_url}:${local.preparer_stable_v}"
  role          = aws_iam_role.preparer_iam.arn
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

resource "aws_s3_bucket_notification" "upload_apkg_notification" {
  bucket = aws_s3_bucket.upload_apkg.id
  lambda_function {
    lambda_function_arn = aws_lambda_function.preparer_func.arn
    events              = ["s3:ObjectCreated:*", "s3:ObjectRemoved:*"]
  }
  depends_on = [aws_lambda_permission.allow_upload_apkg_to_invoke_lambda]
}

resource "aws_ecr_repository" "preparer_repo" {
  name                 = var.preparer_repo_name
  image_tag_mutability = "IMMUTABLE"
}

locals {
  preparer_stable_v = local.versions_data.PREPARER_STABLE_V
}
