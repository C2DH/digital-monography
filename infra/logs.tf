resource "aws_cloudwatch_log_group" "general_purpose_logs" {
  name              = "/aws/dgt-mon/general/${var.environment}"
  retention_in_days = 365
  skip_destroy      = true
}

data "aws_cloudwatch_log_group" "general_purpose_logs" {
  name       = "/aws/dgt-mon/general/${var.environment}"
  depends_on = [aws_cloudwatch_log_group.general_purpose_logs]
}

resource "aws_dynamodb_table" "audit_tbl" {
  name         = var.dgtmon_dev_dyndb_audit_tbl
  hash_key     = "slug"
  billing_mode = "PAY_PER_REQUEST"

  attribute {
    name = "slug"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }
}
