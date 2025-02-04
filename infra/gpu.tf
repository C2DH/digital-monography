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
  name               = "gpu_iam"
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
    resources = ["arn:aws:logs:${var.region}:*:log-group:/aws/*:*"]
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
      "${aws_s3_bucket.metadata_assets_s3.arn}/*"
    ]
    actions = [
      "s3:GetObject",
      "s3:GetObjectAcl",
      "s3:ListBucket",
    ]
  }
}

resource "aws_iam_policy" "gpu" {
  name   = "gpu_policy"
  policy = data.aws_iam_policy_document.gpu.json
}

resource "aws_iam_role_policy_attachment" "gpu" {
  role       = aws_iam_role.gpu_iam.name
  policy_arn = aws_iam_policy.gpu.arn
}

resource "aws_lambda_function" "gpu_func" {
  function_name = "gpu"
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.gpu_repo.repository_url}:${local.gpu_stable_v}"
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
}

resource "aws_ecr_repository" "gpu_repo" {
  name                 = var.gpu_repo_name
  image_tag_mutability = "IMMUTABLE"
}

locals {
  gpu_stable_v = local.versions_data.GPU_STABLE_V
}
