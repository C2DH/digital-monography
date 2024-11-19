resource "aws_s3_bucket" "staticws_dashboard" {
  bucket        = var.staticws_dashboard_bucket_name
  force_destroy = true # TODO: maybe don't destroy when in production, I don't know
}

resource "aws_s3_bucket_website_configuration" "staticws_dashboard" {
  bucket = aws_s3_bucket.staticws_dashboard.id
  index_document {
    suffix = "index.html"
  }
  error_document {
    key = "404.html"
  }
}

resource "aws_s3_bucket_cors_configuration" "dashboard" {
  bucket = aws_s3_bucket.staticws_dashboard.id
  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = ["*"]
    max_age_seconds = 3000
  }
}

resource "aws_s3_bucket_ownership_controls" "staticws_dashboard" {
  bucket = aws_s3_bucket.staticws_dashboard.id
  rule {
    object_ownership = "ObjectWriter"
  }
  depends_on = [aws_s3_bucket_public_access_block.staticws_dashboard]
}

resource "aws_s3_bucket_public_access_block" "staticws_dashboard" {
  bucket                  = aws_s3_bucket.staticws_dashboard.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_acl" "staticws_dashboard" {
  bucket = aws_s3_bucket.staticws_dashboard.id
  acl    = "public-read"
  depends_on = [
    # aws_s3_bucket_public_access_block.staticws_dashboard,
    aws_s3_bucket_ownership_controls.staticws_dashboard
  ]
}

data "aws_iam_policy_document" "public_staticws_dashboard" {
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
      "arn:aws:s3:::${aws_s3_bucket.staticws_dashboard.bucket}",
      "arn:aws:s3:::${aws_s3_bucket.staticws_dashboard.bucket}/*"
    ]
    principals {
      type        = "*"
      identifiers = ["*"]
    }
  }
  depends_on = [aws_s3_bucket_public_access_block.staticws_dashboard]
}

resource "aws_s3_bucket_policy" "public_staticws_dashboard" {
  bucket = aws_s3_bucket.staticws_dashboard.id
  policy = data.aws_iam_policy_document.public_staticws_dashboard.json
}

resource "aws_s3_object" "dashboard_index" {
  bucket       = aws_s3_bucket.staticws_dashboard.id
  key          = "index.html"
  source       = "./staticws/dashboard/out/index.html"
  content_type = "text/html"
}
