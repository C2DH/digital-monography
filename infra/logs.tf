resource "aws_cloudwatch_log_group" "general_purpose_logs" {
  name              = "/${var.project}/general/${var.env}"
  retention_in_days = 365
  # skip_destroy      = true
}

data "aws_cloudwatch_log_group" "general_purpose_logs" {
  name       = "/${var.project}/general/${var.env}"
  depends_on = [aws_cloudwatch_log_group.general_purpose_logs]
}

resource "aws_dynamodb_table" "alerts_tbl" {
  name         = "${var.project}-${var.env}-${var.dgtmon_dev_dyndb_alerts_tbl}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "slug"

  attribute {
    name = "slug"
    type = "S"
  }
}

resource "aws_dynamodb_table" "audit_tbl" {
  name         = "${var.project}-${var.env}-${var.dgtmon_dev_dyndb_audit_tbl}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "slug"
  range_key    = "timestamp"

  attribute {
    name = "slug"
    type = "S"
  }
  attribute {
    name = "timestamp"
    type = "S"
  }
  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }
}

resource "aws_dynamodb_table" "logins_tbl" {
  name         = "${var.project}-${var.env}-${var.dgtmon_dev_dyndb_logins_tbl}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "timestamp"

  attribute {
    name = "timestamp"
    type = "S"
  }
  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }
}
