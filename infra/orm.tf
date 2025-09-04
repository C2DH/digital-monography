# S3

# TODO: versioning, delete protection, encryption, etc. to use as db backup storage
resource "aws_s3_bucket" "admin_data" {
  bucket = "${var.project}-${var.env}-${var.admin_data_bucket_name}"
}

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
  statement {
    sid    = "AllowAccessToS3WithAdminData"
    effect = "Allow"
    resources = [
      aws_s3_bucket.admin_data.arn,
      "${aws_s3_bucket.admin_data.arn}/*",
    ]
    actions = [
      "s3:PutObject",
      "s3:PutObjectAcl",
      "s3:GetObject",
      "s3:GetObjectAcl",
      "s3:ListBucket",
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

resource "aws_lambda_permission" "allow_entrypoint_access_s3_via_vpc_endpoint" {
  statement_id  = "AllowS3AccessViaVPCEndpoint"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.orm_func.arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_vpc_endpoint.s3_endpoint.arn # TODO
}

# resource "aws_lambda_permission" "allow_entrypoint_access_sqs_via_vpc_endpoint" {
#   statement_id  = "AllowSQSAccessViaVPCEndpoint"
#   action        = "lambda:SendMessage"
#   function_name = aws_lambda_function.orm_func.arn
#   principal     = "sqs.amazonaws.com"
#   source_arn    = aws_sqs_queue.entrypoint_to_dropbox.arn # TODO
# }

resource "aws_lambda_function" "orm_func" {
  function_name = "${var.project}-${var.env}-${var.lambda_orm_func}"
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.orm_repo.repository_url}:${local.orm_tag}"
  role          = aws_iam_role.orm_iam.arn
  depends_on = [
    data.aws_cloudwatch_log_group.general_purpose_logs,
    aws_efs_mount_target.efs_mount,
    aws_vpc_endpoint.secretsmanager_endpoint,
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
      DYNAMODB_ALERTS_TBL     = aws_dynamodb_table.alerts_tbl.name
      DYNAMODB_ASSETS_TBL     = aws_dynamodb_table.assets_tbl.name
      DYNAMODB_AUDIT_TBL      = aws_dynamodb_table.audit_tbl.name
      DYNAMODB_CITATIONS_TBL  = aws_dynamodb_table.citations_tbl.name
      DYNAMODB_HEADINGS_TBL   = aws_dynamodb_table.headings_tbl.name
      DYNAMODB_REFS_TBL       = aws_dynamodb_table.refs_tbl.name
      APKG_UPLOAD_BUCKET_NAME = aws_s3_bucket.upload_apkg.bucket
      ADMIN_DATA_BUCKET_NAME  = aws_s3_bucket.admin_data.bucket
      VERIFIER_MSGS           = aws_s3_bucket.verification_msg.bucket
      FLASK_SECRET_KEY        = var.flask_secret_key
      # DASHBOARD_DOMAIN        = aws_s3_bucket.staticws_dashboard.bucket_regional_domain_name
      # DYNAMODB_TOKENS_TBL    = aws_dynamodb_table.tokens_tbl.name
      # DROPBOX_SECRET_ID = data.aws_secretsmanager_secret.github_api_token.id
      # DROPBOX_APP_DIR   = var.dropbox_app_dir
      # DROPBOX_APP_KEY   = var.dropbox_app_key
      # SQS_URL                 = aws_sqs_queue.entrypoint_to_dropbox.url
      # INFRA_ENV         = var.env
    }
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

resource "aws_ecr_repository" "orm_repo" {
  name                 = "${var.project}-dev-${var.microservice_orm}"
  image_tag_mutability = "IMMUTABLE"
  force_delete         = true
}

locals {
  orm_tag = var.env == "main" ? local.versions_data.ORM.STABLE : local.versions_data.ORM.LATEST
}
