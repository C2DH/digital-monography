# Intermediate MD S3

resource "aws_s3_bucket" "ir_apkg_md" {
  bucket        = "${var.project}-${var.env}-${var.ir_apkg_md_bucket_name}"
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
  name = "${var.project}-${var.env}-${var.usr_ir_apkg_md_uploader}"
  # name = "ir-apkg-md-uploader"
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
  # name               = "preparer_iam"
  name               = "${var.project}-${var.env}-${var.role_preparer}"
  assume_role_policy = data.aws_iam_policy_document.assume_preparer_role.json
}

data "aws_iam_policy_document" "preparer" {
  statement {
    sid    = "AllowS3Permissions"
    effect = "Allow"
    resources = [
      aws_s3_bucket.ir_apkg_html.arn,
      aws_s3_bucket.ir_apkg_md.arn,
      aws_s3_bucket.metadata_assets_s3.arn,
      aws_s3_bucket.metadata_refs_s3.arn,
      aws_s3_bucket.upload_apkg.arn,
      "${aws_s3_bucket.ir_apkg_html.arn}/*",
      "${aws_s3_bucket.ir_apkg_md.arn}/*",
      "${aws_s3_bucket.metadata_assets_s3.arn}/*",
      "${aws_s3_bucket.metadata_refs_s3.arn}/*",
      "${aws_s3_bucket.upload_apkg.arn}/*",
      # aws_s3_bucket.verification_msg.arn,
    ]
    actions = [
      "s3:GetObject",
      "s3:GetObjectAcl",
      "s3:DeleteObject",
      "s3:DeleteObjectTagging",
      "s3:ListBucket",
      "s3:PutObject",
      "s3:PutObjectAcl",
    ]
  }
  statement {
    sid    = "AllowMetadataUpload"
    effect = "Allow"
    resources = [
      aws_s3_bucket.metadata_assets_s3.arn,
      "${aws_s3_bucket.metadata_assets_s3.arn}/*",
      aws_s3_bucket.metadata_refs_s3.arn,
      "${aws_s3_bucket.metadata_refs_s3.arn}/*",
    ]
    actions = [
      "s3:GetObject",
      "s3:GetObjectAcl",
      "s3:DeleteObject",
      "s3:DeleteObjectTagging",
      "s3:ListBucket",
      "s3:PutObject",
      "s3:PutObjectAcl",
    ]
  }
  statement {
    sid       = "AllowInvokingLambdas"
    effect    = "Allow"
    resources = ["arn:aws:lambda:${var.region}:*:function:*"]
    actions   = ["lambda:InvokeFunction"]
  }
  statement {
    sid       = "AllowSendingSQSMessages"
    effect    = "Allow"
    resources = [aws_sqs_queue.pre_github_queue.arn]
    actions = [
      "sqs:SendMessage",
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
      aws_dynamodb_table.assets_tbl.arn,
      aws_dynamodb_table.citations_tbl.arn,
      aws_dynamodb_table.headings_tbl.arn,
    ]
    actions = [
      "dynamodb:PutItem",
      "dynamodb:GetItem",
      "dynamodb:UpdateItem",
      "dynamodb:DeleteItem",
      # "dynamodb:Scan",
      # "dynamodb:Query"
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
  # function_name = "preparer"
  function_name = "${var.project}-${var.env}-${var.lambda_preparer_func}"
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.preparer_repo.repository_url}:${local.preparer_tag}"
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
  environment {
    variables = {
      AWS_ACCOUNT_REGION           = var.region
      AWS_ACCOUNT_ID               = var.aws_account_id
      DYNAMODB_ASSETS_TBL          = aws_dynamodb_table.assets_tbl.name
      DYNAMODB_AUDIT_TBL           = aws_dynamodb_table.audit_tbl.name
      DYNAMODB_ALERTS_TBL          = aws_dynamodb_table.alerts_tbl.name
      DYNAMODB_CITATIONS_TBL       = aws_dynamodb_table.citations_tbl.name
      DYNAMODB_HEADINGS_TBL        = aws_dynamodb_table.headings_tbl.name
      IR_APKG_HTML_BUCKET_NAME     = aws_s3_bucket.ir_apkg_html.bucket
      IR_APKG_MD_BUCKET_NAME       = aws_s3_bucket.ir_apkg_md.bucket
      METADATA_ASSETS_BUCKET_NAME  = aws_s3_bucket.metadata_assets_s3.bucket
      SQS_GITHUB_FIFO_TRIGGER_NAME = aws_sqs_queue.pre_github_queue.name
    }
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
  name                 = "${var.project}-dev-${var.microservice_preparer}"
  image_tag_mutability = "IMMUTABLE"
  force_delete         = true
}

locals {
  preparer_tag = var.env == "main" ? local.versions_data.PREPARER.STABLE : local.versions_data.PREPARER.LATEST
}
