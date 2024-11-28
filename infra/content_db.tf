resource "aws_dynamodb_table" "statuses_tbl" {
  name         = var.dgtmon_dev_dyndb_assets_tbl
  hash_key     = "slug"
  billing_mode = "PAY_PER_REQUEST"

  attribute {
    name = "slug"
    type = "S"
  }
}
