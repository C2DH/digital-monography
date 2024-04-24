resource "aws_s3_bucket" "staticws_wip" {
  bucket        = var.staticws_wip_bucket_name
  force_destroy = true # TODO: don't destroy when in production
}

resource "aws_s3_bucket_website_configuration" "staticws_wip" {
  bucket = aws_s3_bucket.staticws_wip.id
  index_document {
    suffix = "index.html"
  }
  error_document {
    key = "error.html"
  }
}

# resource "aws_s3_bucket_versioning" "staticws_wip" {
#   bucket = aws_s3_bucket.staticws_wip.id
#   versioning_configuration {
#     status = "Enabled"
#   }
# }

resource "aws_s3_bucket_cors_configuration" "prod_media" {
  bucket = aws_s3_bucket.staticws_wip.id
  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = ["*"]
    max_age_seconds = 3000
  }
}

resource "aws_s3_bucket_ownership_controls" "staticws_wip" {
  bucket = aws_s3_bucket.staticws_wip.id
  rule {
    object_ownership = "ObjectWriter"
  }
  depends_on = [aws_s3_bucket_public_access_block.staticws_wip]
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
    # aws_s3_bucket_public_access_block.staticws_wip,
    aws_s3_bucket_ownership_controls.staticws_wip
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
  depends_on = [aws_s3_bucket_public_access_block.staticws_wip]
}

resource "aws_s3_bucket_policy" "public_staticws_wip" {
  bucket = aws_s3_bucket.staticws_wip.id
  policy = data.aws_iam_policy_document.public_staticws_wip.json
}

resource "aws_s3_object" "index_html" {
  bucket       = aws_s3_bucket.staticws_wip.id
  key          = "index.html"
  source       = "./staticws/index.html"
  content_type = "text/html"
}
