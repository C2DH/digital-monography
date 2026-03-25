# How to manage access to the external S3 bucket:
#  * Change user ARNs in the assume role policy
#  * Assume the role before accessing the bucket

# Get current AWS account ID
data "aws_caller_identity" "current_aws_acc" {}

# Never change the name of the role, as the ARN will be shared with the external organization
resource "aws_iam_role" "access_built_jb" {
  name        = "${var.project}-${var.env}-role-external-s3-built-jb"
  description = "IAM Role to allow access an external S3 bucket for uploading built Jupyter Books"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = [
            aws_iam_user.cli_PAK.arn,
          ]
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "access_built_jb" {
  name = "${var.project}-${var.env}-policy-external-s3-built-jb"
  role = aws_iam_role.access_built_jb.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${var.built_jb_bucket_arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = "${var.built_jb_bucket_arn}"
      }
    ]
  })
}

# Note the ARN of the role will not change if the role is destroyed and reapplied
output "access_built_jb_role_arn" {
  description = "ARN of the role to share with the external organization"
  value       = aws_iam_role.access_built_jb.arn
}

output "access_built_jb_assume_role_instructions" {
  description = "Instructions for assuming the role"
  value       = <<-EOT
    To assume this role, use the following AWS CLI command:

    aws sts assume-role \
      --role-arn ${aws_iam_role.access_built_jb.arn} \
      --role-session-name my-session

    This will return temporary credentials (AccessKeyId, SecretAccessKey, SessionToken).

    Then use these credentials to access the external S3 bucket:

    aws s3 ls s3://${var.built_jb_bucket_name}/ \
      --access-key <AccessKeyId> \
      --secret-key <SecretAccessKey> \
      --session-token <SessionToken>

    Alternatively, configure your AWS CLI profile with the assumed role credentials:

    [profile external-access]
    role_arn = ${aws_iam_role.access_built_jb.arn}
    source_profile = default

    Then use: aws s3 ls s3://${var.built_jb_bucket_name}/ --profile external-access
  EOT
}
