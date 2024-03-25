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

resource "aws_lambda_function" "builder_func" {
  filename      = "./../src/builder/builder.zip"
  function_name = "builder"
  role          = aws_iam_role.builder_iam.arn
  depends_on    = [aws_cloudwatch_log_group.general_purpose_logs]
  handler       = "main.lambda_handler"
  runtime       = "python3.12"
  timeout       = 900
  memory_size   = 512
}

resource "aws_s3_bucket_notification" "ir_apkg_md_notification" {
  bucket = aws_s3_bucket.ir_apkg_md.id
  lambda_function {
    lambda_function_arn = aws_lambda_function.builder_func.arn
    events              = ["s3:ObjectCreated:*", "s3:ObjectRemoved:*"]
  }
  depends_on = [aws_lambda_permission.allow_ir_apkg_md_to_invoke_lambda]
}
