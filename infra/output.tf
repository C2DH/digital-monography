output "website_url" {
  value = "http://${aws_s3_bucket.staticws_wip.bucket}.s3-website.${var.region}.amazonaws.com"
}

output "gp_log_group_arn" {
  value = aws_cloudwatch_log_group.general_purpose_logs.arn
}

output "gp_log_group_name" {
  value = aws_cloudwatch_log_group.general_purpose_logs.name
}

output "upload_apkg_bucket_name" {
  value = aws_s3_bucket.upload_apkg.bucket
}

output "ir_apkg_html_bucket_name" {
  value = aws_s3_bucket.ir_apkg_html.bucket
}

output "ir_apkg_md_bucket_name" {
  value = aws_s3_bucket.ir_apkg_md.bucket
}

output "staticws_wip_bucket_name" {
  value = aws_s3_bucket.staticws_wip.bucket
}
