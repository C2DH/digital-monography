resource "aws_dynamodb_table" "assets_tbl" {
  name         = var.dgtmon_dev_dyndb_assets_tbl
  hash_key     = "slug"
  billing_mode = "PAY_PER_REQUEST"

  attribute {
    name = "slug"
    type = "S"
  }
}

resource "aws_dynamodb_table" "headings_tbl" {
  name         = var.dgtmon_dev_dyndb_headings_tbl
  hash_key     = "slug"
  billing_mode = "PAY_PER_REQUEST"

  attribute {
    name = "slug"
    type = "S"
  }
}

resource "aws_dynamodb_table" "citations_tbl" {
  name         = var.dgtmon_dev_dyndb_citations_tbl
  hash_key     = "slug"
  billing_mode = "PAY_PER_REQUEST"

  attribute {
    name = "slug"
    type = "S"
  }
}
