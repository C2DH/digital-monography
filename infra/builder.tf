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

## Lambda (builder)

data "aws_iam_policy_document" "assume_builder_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "builder_iam" {
  name               = "builder_iam"
  assume_role_policy = data.aws_iam_policy_document.assume_builder_role.json
}

data "aws_iam_policy_document" "builder" {
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
    resources = ["arn:aws:logs:${var.region}:*:log-group:/aws/lambda/*:*"]
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
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

resource "aws_iam_policy" "builder" {
  name   = "builder_policy"
  policy = data.aws_iam_policy_document.builder.json
}

resource "aws_iam_role_policy_attachment" "builder" {
  role       = aws_iam_role.builder_iam.name
  policy_arn = aws_iam_policy.builder.arn
}

resource "aws_lambda_permission" "allow_ir_apkg_md_to_invoke_lambda" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.builder_func.arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.ir_apkg_md.arn
}

resource "aws_lambda_permission" "allow_builder_access_s3_via_vpc_endpoint" {
  statement_id  = "AllowS3AccessViaVPCEndpoint"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.builder_func.arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_vpc_endpoint.s3_endpoint.arn
}

resource "aws_lambda_function" "builder_func" {
  filename         = "./../src/builder/builder.zip"
  function_name    = "builder"
  role             = aws_iam_role.builder_iam.arn
  source_code_hash = filebase64sha256("./../src/builder/builder.zip")
  depends_on = [
    data.aws_cloudwatch_log_group.general_purpose_logs,
    aws_efs_mount_target.efs_mount
  ]
  handler     = "main.lambda_handler"
  runtime     = "python3.12"
  timeout     = 900
  memory_size = 1024
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

resource "aws_s3_bucket_notification" "ir_apkg_md_notification" {
  bucket = aws_s3_bucket.ir_apkg_md.id
  lambda_function {
    lambda_function_arn = aws_lambda_function.builder_func.arn
    events              = ["s3:ObjectCreated:*", "s3:ObjectRemoved:*"]
  }
  depends_on = [aws_lambda_permission.allow_ir_apkg_md_to_invoke_lambda]
}
