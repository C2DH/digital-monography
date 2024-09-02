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

## Intermediate HTML S3

resource "aws_s3_bucket" "ir_apkg_html" {
  bucket        = var.ir_apkg_html_bucket_name
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

## Uploader

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

## SQS (Lambda trigger)

resource "aws_sqs_queue" "pre_builder_queue" {
  name                        = "${var.sqs_builder_trigger}.fifo"
  fifo_queue                  = true
  receive_wait_time_seconds   = 15 # TODO: once on DGT infra, reduce wait time
  delay_seconds               = 5
  content_based_deduplication = true
  max_message_size            = 1024 # 1 KiB
  message_retention_seconds   = 3600 # 1 hour
}

resource "aws_lambda_event_source_mapping" "pre_builder" {
  event_source_arn = aws_sqs_queue.pre_builder_queue.arn
  function_name    = aws_lambda_function.builder_func.arn
}

# resource "aws_s3_bucket_notification" "ir_apkg_md_notification" {
#   bucket = aws_s3_bucket.ir_apkg_md.id
#   lambda_function {
#     lambda_function_arn = aws_lambda_function.builder_func.arn
#     events              = ["s3:ObjectCreated:*", "s3:ObjectRemoved:*"]
#   }
#   depends_on = [aws_lambda_permission.allow_ir_apkg_md_to_invoke_lambda]
# }

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
    resources = ["arn:aws:logs:${var.region}:*:log-group:/aws/*:*"]
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
  }
  statement {
    sid       = "AllowReceivingSQSMessages"
    effect    = "Allow"
    resources = [aws_sqs_queue.pre_builder_queue.arn]
    actions = [
      "sqs:DeleteMessage",
      "sqs:ReceiveMessage",
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
  function_name = "builder"
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.builder_repo.repository_url}:${local.builder_stable_v}"
  role          = aws_iam_role.builder_iam.arn
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

# resource "aws_s3_bucket_notification" "ir_apkg_md_notification" {
#   bucket = aws_s3_bucket.ir_apkg_md.id
#   lambda_function {
#     lambda_function_arn = aws_lambda_function.builder_func.arn
#     events              = ["s3:ObjectCreated:*", "s3:ObjectRemoved:*"]
#   }
#   depends_on = [aws_lambda_permission.allow_ir_apkg_md_to_invoke_lambda]
# }

resource "aws_ecr_repository" "builder_repo" {
  name                 = var.builder_repo_name
  image_tag_mutability = "IMMUTABLE"
}

locals {
  builder_stable_v = local.versions_data.BUILDER_STABLE_V
}
