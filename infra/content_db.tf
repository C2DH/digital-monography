# TODO: rename content_db to metadata

resource "aws_dynamodb_table" "assets_tbl" {
  name         = var.dgtmon_dev_dyndb_assets_tbl
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

resource "aws_s3_bucket" "metadata_assets_s3" {
  bucket        = var.metadata_assets_bucket_name
  force_destroy = true
}

resource "aws_s3_bucket_cors_configuration" "metadata_assets_s3_config" {
  bucket = aws_s3_bucket.metadata_assets_s3.id

  cors_rule {
    allowed_methods = ["HEAD", "GET"]
    allowed_origins = ["*"]
    max_age_seconds = 43200
  }
}

# data "aws_iam_policy_document" "metadata_assets_s3_policy" {
#   statement {
#     actions = [
#       "s3:*" # TODO: limit
#     ]
#     resources = [
#       "arn:aws:s3:::${aws_s3_bucket.metadata_assets_s3.bucket}",
#       "arn:aws:s3:::${aws_s3_bucket.metadata_assets_s3.bucket}/*"
#     ]
#     principals {
#       type        = "AWS"
#       identifiers = [aws_iam_user.apkg_uploader.arn]
#     }
#   }
# }

# resource "aws_s3_bucket_policy" "metadata_assets_s3_policy" {
#   bucket = aws_s3_bucket.metadata_assets_s3.id
#   policy = data.aws_iam_policy_document.metadata_assets_s3_policy.json
# }
