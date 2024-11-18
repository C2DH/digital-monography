resource "aws_dynamodb_table" "statuses_tbl" {
  name         = var.dgtmon_dev_dyndb_statuses_tbl
  hash_key     = "uuid"
  billing_mode = "PAY_PER_REQUEST"

  attribute {
    name = "uuid"
    type = "S"
  }
}
