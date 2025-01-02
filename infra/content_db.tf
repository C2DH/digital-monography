resource "aws_dynamodb_table" "assets_tbl" {
  name         = var.dgtmon_dev_dyndb_assets_tbl
  hash_key     = "slug"
  billing_mode = "PAY_PER_REQUEST"

  attribute {
    name = "slug"
    type = "S"
  }
  attribute {
    name = "fn"
    type = "S"
  }

}

resource "aws_dynamodb_table" "headings_tbl" {
  name         = var.dgtmon_dev_dyndb_headings_tbl
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "slug"
  range_key    = "fn"

  attribute {
    name = "slug"
    type = "S"
  }
  attribute {
    name = "fn"
    type = "S"
  }

}

resource "aws_dynamodb_table" "citations_tbl" {
  name         = var.dgtmon_dev_dyndb_citations_tbl
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "slug"
  range_key    = "fn"

  attribute {
    name = "slug"
    type = "S"
  }
  attribute {
    name = "fn"
    type = "S"
  }

}

resource "aws_dynamodb_table" "warnings_tbl" {
  name         = var.dgtmon_dev_dyndb_warnings_tbl
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "slug"
  range_key    = "fn"

  attribute {
    name = "slug"
    type = "S"
  }
  attribute {
    name = "fn"
    type = "S"
  }

}

