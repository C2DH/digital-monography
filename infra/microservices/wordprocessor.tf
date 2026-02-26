# resource "aws_lambda_function" "wordprocessor_func" {
#   ...
#   environment {
#     variables = {
#       DYNAMODB_AUDIT_TBL            = aws_dynamodb_table.audit_tbl.name
#       DYNAMODB_ALERTS_TBL           = aws_dynamodb_table.alerts_tbl.name
#     }
#   }
# }
