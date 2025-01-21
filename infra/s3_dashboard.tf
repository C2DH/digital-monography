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

module "dashboard_files" {
  source   = "hashicorp/dir/template"
  base_dir = "./staticws/nextjs/out/"
}

resource "aws_s3_object" "dashboard_dir" {
  for_each     = module.dashboard_files.files
  bucket       = aws_s3_bucket.staticws_dashboard.id
  key          = each.key
  content_type = each.value.content_type
  # The template_files module guarantees that only one of these two attributes
  # will be set for each file, depending on whether it is an in-memory template
  # rendering result or a static file on disk.
  source  = each.value.source_path
  content = each.value.content
  # Unless the bucket has encryption enabled, the ETag of each object is an
  # MD5 hash of that object.
  etag = each.value.digests.md5
}
