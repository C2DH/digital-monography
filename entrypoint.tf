resource "aws_lambda_function" "preparer_func" {
  function_name = "preparer"
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.preparer_repo.repository_url}:${local.preparer_stable_v}"
  role          = aws_iam_role.preparer_iam.arn
  depends_on = [
    data.aws_cloudwatch_log_group.general_purpose_logs,
    # aws_efs_mount_target.efs_mount
  ]
  architectures = ["x86_64"]
  timeout       = 900
  memory_size   = 1024
  logging_config {
    log_group  = data.aws_cloudwatch_log_group.general_purpose_logs.name
    log_format = "JSON"
  }
  #   file_system_config {
  #     arn              = aws_efs_access_point.efs_access_point.arn
  #     local_mount_path = "/mnt/efs"
  #   }
  #   vpc_config {
  #     subnet_ids         = [aws_subnet.efs_public.id]
  #     security_group_ids = [aws_security_group.efs_access_sg.id]
  #   }
}

# resource "aws_s3_bucket_notification" "upload_apkg_notification" {
#   bucket = aws_s3_bucket.upload_apkg.id
#   lambda_function {
#     lambda_function_arn = aws_lambda_function.preparer_func.arn
#     events              = ["s3:ObjectCreated:*", "s3:ObjectRemoved:*"]
#   }
#   depends_on = [aws_lambda_permission.allow_upload_apkg_to_invoke_lambda]
# }

resource "aws_ecr_repository" "preparer_repo" {
  name                 = var.preparer_repo_name
  image_tag_mutability = "IMMUTABLE"
}

locals {
  preparer_stable_v = local.versions_data.ENTRYPOINT_STABLE_V
}
