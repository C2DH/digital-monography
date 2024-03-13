# Comment to triger DevOps pipeline 0.4

resource "aws_s3_bucket" "upload_apkg" {
  bucket        = var.upload_apkg_bucket_name
  force_destroy = true
}

# resource "aws_s3_bucket_versioning" "upload_apkg" {
#   bucket = aws_s3_bucket.upload_apkg.id
#   versioning_configuration {
#     status = "Enabled"
#   }
# }

data "aws_iam_policy_document" "public_upload_apkg" {
  statement {
    actions = [
      "s3:*"
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

# Uploader

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

## Lambda (builder)

data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "iam_for_lambda" {
  name               = "iam_for_lambda"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

data "aws_iam_policy_document" "builder" {
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

resource "aws_iam_policy" "builder" {
  name   = "builder_policy"
  policy = data.aws_iam_policy_document.builder.json
}

resource "aws_iam_role_policy_attachment" "builder" {
  role       = aws_iam_role.iam_for_lambda.name
  policy_arn = aws_iam_policy.builder.arn
}

resource "aws_lambda_permission" "allow_bucket" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.builder_func.arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.upload_apkg.arn
}

resource "aws_cloudwatch_log_group" "builder_logs" {
  name              = "/aws/lambda/builder"
  retention_in_days = 120
  lifecycle {
    prevent_destroy = false
  }
}

resource "aws_lambda_function" "builder_func" {
  filename      = "./../src/builder/builder.zip"
  function_name = "builder"
  role          = aws_iam_role.iam_for_lambda.arn
  depends_on    = [aws_cloudwatch_log_group.builder_logs]
  handler       = "main.lambda_handler"
  runtime       = "python3.12"
  # timeout       = 30
  # memory_size   = 128
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.upload_apkg.id
  lambda_function {
    lambda_function_arn = aws_lambda_function.builder_func.arn
    events              = ["s3:ObjectCreated:*", "s3:ObjectRemoved:*"]
  }
  depends_on = [aws_lambda_permission.allow_bucket]
}
