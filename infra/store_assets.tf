resource "aws_s3_bucket" "static_assets" {
  bucket = "${var.project}-${var.env}-${var.static_assets_bucket_name}"
}

resource "aws_s3_bucket_public_access_block" "static_assets" {
  bucket = aws_s3_bucket.static_assets.id

  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "static_assets_public_read" {
  bucket = aws_s3_bucket.static_assets.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = ["s3:GetObject"]
        Resource  = "${aws_s3_bucket.static_assets.arn}/*"
      }
    ]
  })
  depends_on = [aws_s3_bucket_public_access_block.static_assets]
}
