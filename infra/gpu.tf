## Lambda (gpu)

data "aws_iam_policy_document" "assume_gpu_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "gpu_iam" {
  # name               = "gpu_iam"
  name               = "${var.project}-${var.env}-${var.role_gpu}"
  assume_role_policy = data.aws_iam_policy_document.assume_gpu_role.json
}

data "aws_iam_policy_document" "gpu" {
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
    resources = ["arn:aws:logs:${var.region}:*:log-group:*:*"]
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
  }
  statement {
    sid    = "AllowGettingObjectsFromS3"
    effect = "Allow"
    resources = [
      "${aws_s3_bucket.upload_apkg.arn}",
      "${aws_s3_bucket.upload_apkg.arn}/*",
      "${aws_s3_bucket.verification_msg.arn}",
      "${aws_s3_bucket.verification_msg.arn}/*",
      "${aws_s3_bucket.metadata_assets_s3.arn}",
      "${aws_s3_bucket.metadata_assets_s3.arn}/*",
      "${aws_s3_bucket.metadata_refs_s3.arn}",
      "${aws_s3_bucket.metadata_refs_s3.arn}/*"
    ]
    actions = [
      "s3:GetObject",
      "s3:GetObjectAcl",
      "s3:ListBucket",
    ]
  }
}

resource "aws_iam_policy" "gpu" {
  # name   = "gpu_policy"
  name   = "${var.project}-${var.env}-${var.policy_gpu}"
  policy = data.aws_iam_policy_document.gpu.json
}

resource "aws_iam_role_policy_attachment" "gpu" {
  role       = aws_iam_role.gpu_iam.name
  policy_arn = aws_iam_policy.gpu.arn
}

resource "aws_lambda_function" "gpu_func" {
  # function_name = "gpu"
  function_name = "${var.project}-${var.env}-${var.lambda_gpu_func}"
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.gpu_repo.repository_url}:${local.gpu_tag}"
  role          = aws_iam_role.gpu_iam.arn
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
      APKG_UPLOAD_BUCKET_NAME     = aws_s3_bucket.upload_apkg.bucket
      METADATA_ASSETS_BUCKET_NAME = aws_s3_bucket.metadata_assets_s3.bucket
      METADATA_REFS_BUCKET_NAME   = aws_s3_bucket.metadata_refs_s3.bucket
      VERIFIER_DOC_MSGS           = aws_s3_bucket.verification_msg.bucket
    }
  }
}

resource "aws_ecr_repository" "gpu_repo" {
  name                 = "${var.project}-dev-${var.microservice_gpu}"
  image_tag_mutability = "IMMUTABLE"
  force_delete         = true
}

locals {
  gpu_tag = var.env == "main" ? local.versions_data.GPU.STABLE : local.versions_data.GPU.LATEST
}
