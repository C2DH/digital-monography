resource "aws_s3_bucket" "staticws_wip" {
  bucket = var.staticws_wip_bucket_name
}

resource "aws_s3_bucket_website_configuration" "staticws_wip" {
  bucket = aws_s3_bucket.staticws_wip.id
  index_document {
    suffix = "index.html"
  }
  error_document {
    key = "index.html"
  }
}

# resource "aws_s3_bucket_versioning" "staticws_wip" {
#   bucket = aws_s3_bucket.staticws_wip.id
#   versioning_configuration {
#     status = "Enabled"
#   }
# }

resource "aws_s3_bucket_ownership_controls" "staticws_wip" {
  bucket = aws_s3_bucket.staticws_wip.id
  rule {
    object_ownership = "ObjectWriter"
  }
}

resource "aws_s3_bucket_public_access_block" "staticws_wip" {
  bucket                  = aws_s3_bucket.staticws_wip.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_acl" "staticws_wip" {
  bucket = aws_s3_bucket.staticws_wip.id
  acl    = "public-read"
  depends_on = [
    aws_s3_bucket_public_access_block.staticws_wip,
  ]
}

data "aws_iam_policy_document" "public_staticws_wip" {
  statement {
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:PutObjectAcl",
      "s3:PutBucketCORS",
      "s3:PutBucketWebsite",
      "s3:ListBucket"
    ]
    resources = [
      "arn:aws:s3:::${aws_s3_bucket.staticws_wip.bucket}",
      "arn:aws:s3:::${aws_s3_bucket.staticws_wip.bucket}/*"
    ]
    principals {
      type        = "*"
      identifiers = ["*"]
    }
  }
}

resource "aws_s3_bucket_policy" "public_staticws_wip" {
  bucket = aws_s3_bucket.staticws_wip.id
  policy = data.aws_iam_policy_document.public_staticws_wip.json
}

resource "aws_s3_object" "index_html" {
  bucket       = aws_s3_bucket.staticws_wip.id
  key          = "index.html"
  source       = "./../staticws/index.html"
  content_type = "text/html"
}
