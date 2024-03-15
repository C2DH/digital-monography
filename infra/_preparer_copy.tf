# resource "aws_s3_bucket" "ir_apkg_html" {
#   bucket        = var.ir_apkg_html_bucket_name
#   force_destroy = true
# }

# resource "aws_s3_bucket" "ir_apkg_md" {
#   bucket        = var.ir_apkg_md_bucket_name
#   force_destroy = true
# }

# data "aws_iam_policy_document" "ir_html" {
#   statement {
#     actions = [
#       "s3:GetObject",
#       "s3:PutObject",
#     ]
#     resources = [
#       "arn:aws:s3:::${aws_s3_bucket.ir_apkg_html.bucket}",
#       "arn:aws:s3:::${aws_s3_bucket.ir_apkg_html.bucket}/*",
#     ]
#     principals {
#       type        = "AWS"
#       identifiers = [aws_iam_user.ir_uploader.arn]
#     }
#   }
# }

# data "aws_iam_policy_document" "ir_md" {
#   statement {
#     actions = [
#       "s3:GetObject",
#       "s3:PutObject",
#     ]
#     resources = [
#       "arn:aws:s3:::${aws_s3_bucket.ir_apkg_md.bucket}",
#       "arn:aws:s3:::${aws_s3_bucket.ir_apkg_md.bucket}/*"
#     ]
#     principals {
#       type        = "AWS"
#       identifiers = [aws_iam_user.ir_uploader.arn]
#     }
#   }
# }

# # Uploader

# resource "aws_s3_bucket_policy" "ir_html" {
#   bucket = aws_s3_bucket.ir_apkg_html.id
#   policy = data.aws_iam_policy_document.ir_html.json
# }

# resource "aws_iam_user" "ir_uploader" {
#   name = "ir-uploader"
# }

# resource "aws_iam_access_key" "ir_uploader" {
#   user = aws_iam_user.ir_uploader.name
# }

# output "ir_uploader_id" {
#   value = aws_iam_access_key.ir_uploader.id
# }

# ## Lambda (preparer)

# data "aws_iam_policy_document" "assume_role" {
#   statement {
#     effect = "Allow"
#     principals {
#       type        = "Service"
#       identifiers = ["lambda.amazonaws.com"]
#     }
#     actions = ["sts:AssumeRole"]
#   }
# }

# resource "aws_iam_role" "iam_for_lambda" {
#   name               = "iam_for_lambda"
#   assume_role_policy = data.aws_iam_policy_document.assume_role.json
# }

# data "aws_iam_policy_document" "preparer" {
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
#     resources = ["arn:aws:logs:${var.region}:*:log-group:/aws/lambda/*:*"]
#     actions = [
#       "logs:CreateLogStream",
#       "logs:PutLogEvents",
#     ]
#   }
# }

# resource "aws_iam_policy" "preparer" {
#   name   = "preparer_policy"
#   policy = data.aws_iam_policy_document.preparer.json
# }

# resource "aws_iam_role_policy_attachment" "preparer" {
#   role       = aws_iam_role.iam_for_lambda.name
#   policy_arn = aws_iam_policy.preparer.arn
# }

# resource "aws_lambda_permission" "allow_ir_apkg_html" {
#   statement_id  = "AllowExecutionFromS3Bucket"
#   action        = "lambda:InvokeFunction"
#   function_name = aws_lambda_function.preparer_func.arn
#   principal     = "s3.amazonaws.com"
#   source_arn    = aws_s3_bucket.ir_apkg_html.arn
# }

# resource "aws_lambda_permission" "allow_ir_apkg_md" {
#   statement_id  = "AllowExecutionFromS3Bucket"
#   action        = "lambda:InvokeFunction"
#   function_name = aws_lambda_function.preparer_func.arn
#   principal     = "s3.amazonaws.com"
#   source_arn    = aws_s3_bucket.ir_apkg_md.arn
# }

# resource "aws_cloudwatch_log_group" "preparer_logs" {
#   name              = "/aws/lambda/preparer"
#   retention_in_days = 120
#   lifecycle {
#     prevent_destroy = false
#   }
# }

# resource "aws_lambda_function" "preparer_func" {
#   filename      = "./../src/preparer/preparer.zip"
#   function_name = "preparer"
#   role          = aws_iam_role.iam_for_lambda.arn
#   depends_on    = [aws_cloudwatch_log_group.preparer_logs]
#   handler       = "main.lambda_handler"
#   runtime       = "python3.12"
#   # timeout       = 30
#   # memory_size   = 128
# }

# resource "aws_s3_bucket_notification" "bucket_notification" {
#   bucket = aws_s3_bucket.upload_ir.id
#   lambda_function {
#     lambda_function_arn = aws_lambda_function.preparer_func.arn
#     events              = ["s3:ObjectCreated:*", "s3:ObjectRemoved:*"]
#   }
#   depends_on = [
#     aws_lambda_permission.allow_ir_apkg_html,
#     aws_lambda_permission.allow_ir_apkg_md
#   ]
# }
