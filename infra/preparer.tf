# Upload S3

resource "aws_s3_bucket" "upload_apkg" {
  bucket        = var.upload_apkg_bucket_name
  force_destroy = true
}

data "aws_iam_policy_document" "public_upload_apkg" {
  statement {
    actions = [
      "s3:*" # TODO: limit
    ]
    resources = [
      "arn:aws:s3:::${aws_s3_bucket.upload_apkg.bucket}",
      "arn:aws:s3:::${aws_s3_bucket.upload_apkg.bucket}/*"
    ]
    principals {
      type        = "AWS"
      identifiers = [aws_iam_user.apkg_uploader.arn]
    }
  }
}

# Intermediate HTML S3

resource "aws_s3_bucket" "ir_apkg_html" {
  bucket = var.ir_apkg_html_bucket_name
  force_destroy = true
}

data "aws_iam_policy_document" "ir_apkg_html_policy" {
  statement {
    actions = [
      "s3:*" # TODO: limit
    ]
    resources = [
      "arn:aws:s3:::${aws_s3_bucket.ir_apkg_html.bucket}",
      "arn:aws:s3:::${aws_s3_bucket.ir_apkg_html.bucket}/*"
    ]
    principals {
      type        = "AWS"
      identifiers = [aws_iam_user.apkg_uploader.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "ir_apkg_html_policy" {
  bucket = aws_s3_bucket.ir_apkg_html.id
  policy = data.aws_iam_policy_document.ir_apkg_html_policy.json
}

# # Uploader

resource "aws_s3_bucket_policy" "public_upload_apkg" {
  bucket = aws_s3_bucket.upload_apkg.id
  policy = data.aws_iam_policy_document.public_upload_apkg.json
}

resource "aws_iam_user" "apkg_uploader" {
  name = "apkg-uploader"
}

resource "aws_iam_access_key" "apkg_uploader" {
  user = aws_iam_user.apkg_uploader.name
}

output "apkg_uploader_id" {
  value = aws_iam_access_key.apkg_uploader.id
}

# ## Lambda (preparer)

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
    resources = ["arn:aws:logs:${var.region}:*:log-group:/aws/lambda/*:*"]
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
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

resource "aws_cloudwatch_log_group" "preparer_logs" {
  name              = "/aws/lambda/preparer"
  retention_in_days = 120
  lifecycle {
    prevent_destroy = false
  }
}

resource "aws_lambda_function" "preparer_func" {
  filename      = "./../src/preparer/preparer.zip"
  function_name = "preparer"
  role          = aws_iam_role.preparer_iam.arn
  depends_on    = [aws_cloudwatch_log_group.preparer_logs]
  handler       = "main.lambda_handler"
  runtime       = "python3.12"
  timeout       = 900
  memory_size   = 512
}

resource "aws_s3_bucket_notification" "upload_apkg_notification" {
  bucket = aws_s3_bucket.upload_apkg.id
  lambda_function {
    lambda_function_arn = aws_lambda_function.preparer_func.arn
    events              = ["s3:ObjectCreated:*", "s3:ObjectRemoved:*"]
  }
  depends_on = [aws_lambda_permission.allow_upload_apkg_to_invoke_lambda]
}
