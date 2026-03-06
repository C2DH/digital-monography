# output "website_url" {
#   value = "http://${aws_s3_bucket.staticws_wip.bucket}.s3-website.${var.region}.amazonaws.com"
# }

output "gp_log_group_arn" {
  value = data.aws_cloudwatch_log_group.general_purpose_logs.arn
}

output "gp_log_group_name" {
  value = data.aws_cloudwatch_log_group.general_purpose_logs.name
}

# output "upload_apkg_bucket_name" {
#   value = aws_s3_bucket.upload_apkg.bucket
# }

# output "ir_apkg_html_bucket_name" {
#   value = aws_s3_bucket.ir_apkg_html.bucket
# }

# output "ir_apkg_md_bucket_name" {
#   value = aws_s3_bucket.ir_apkg_md.bucket
# }

# output "archive_apkg_all_bucket_name" {
#   value = aws_s3_bucket.archive_apkg_all.bucket
# }

# output "staticws_wip_bucket_name" {
#   value = aws_s3_bucket.staticws_wip.bucket
# }

output "github_api_token" {
  value     = data.aws_secretsmanager_secret_version.github_api_token.secret_string
  sensitive = true
}

output "websvr_vm_connect" {
  value = "aws ssm start-session --target ${aws_instance.websvr.id}"
}

output "websvr_instance_id" {
  value = aws_instance.websvr.id
}

output "websvr_public_ip" {
  value = aws_instance.websvr.public_ip
}

output "websvr_public_dns" {
  value = aws_instance.websvr.public_dns
}

output "static_assets_bucket_name" {
  value = aws_s3_bucket.static_assets.bucket
}

output "static_assets_bucket_url" {
  value = "https://${aws_s3_bucket.static_assets.bucket}.s3.${var.region}.amazonaws.com"
}
