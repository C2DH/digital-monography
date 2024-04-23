# resource "aws_cloudwatch_log_group" "general_purpose_logs" {
#   name              = "/aws/dgt-mon/general/${var.environment}"
#   retention_in_days = 365
#   skip_destroy      = true
# }

data "aws_cloudwatch_log_group" "general_purpose_logs" {
  name = "/aws/dgt-mon/general/${var.environment}"
  # depends_on = [aws_cloudwatch_log_group.general_purpose_logs]
}
