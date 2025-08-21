## Lambda (orm)

data "aws_iam_policy_document" "assume_orm_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "orm_iam" {
  # name               = "orm_iam"
  name               = "${var.project}-${var.env}-${var.role_orm}"
  assume_role_policy = data.aws_iam_policy_document.assume_orm_role.json
}

data "aws_iam_policy_document" "orm" {
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
}

resource "aws_iam_policy" "orm" {
  name   = "orm_policy"
  policy = data.aws_iam_policy_document.orm.json
}

resource "aws_iam_role_policy_attachment" "orm" {
  role       = aws_iam_role.orm_iam.name
  policy_arn = aws_iam_policy.orm.arn
}

resource "aws_lambda_function" "orm_func" {
  function_name = "${var.project}-${var.env}-${var.lambda_orm_func}"
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.orm_repo.repository_url}:${local.orm_tag}"
  role          = aws_iam_role.orm_iam.arn
  depends_on = [
    data.aws_cloudwatch_log_group.general_purpose_logs,
    # aws_efs_mount_target.efs_mount
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
      #   DASHBOARD_DOMAIN = aws_s3_bucket.staticws_dashboard.bucket_regional_domain_name
      #   FLASK_SECRET_KEY = var.flask_secret_key
    }
  }
}

resource "aws_ecr_repository" "orm_repo" {
  name                 = "${var.project}-dev-${var.microservice_orm}"
  image_tag_mutability = "IMMUTABLE"
  force_delete         = true
}

locals {
  orm_tag = var.env == "main" ? local.versions_data.ORM.STABLE : local.versions_data.ORM.LATEST
}
