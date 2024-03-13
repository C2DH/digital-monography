output "website_url" {
  value = "http://${aws_s3_bucket.staticws_wip.bucket}.s3-website.${var.region}.amazonaws.com"
}

output "staticws_wip_bucket_name" {
  value = aws_s3_bucket.staticws_wip.bucket
}

output "upload_apkg_bucket_name" {
  value = aws_s3_bucket.upload_apkg.bucket
}
