output "website_url" {
  value = "http://${aws_s3_bucket.staticws_wip.bucket}.s3-website.${var.region}.amazonaws.com"
}

# output "upload_apkg_bucket_name" {
#   value = aws_s3_bucket.upload_apkg.bucket
# }

output "ir_apkg_md_bucket_name" {
  value = aws_s3_bucket.ir_apkg_md.bucket
}

output "staticws_wip_bucket_name" {
  value = aws_s3_bucket.staticws_wip.bucket
}
