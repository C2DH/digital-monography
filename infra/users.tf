resource "aws_iam_group" "devs" {
  name = "${var.project}-shared-${var.group_devs}"
  path = "/users/"
}

resource "aws_iam_policy" "dev_ecr" {
  name = "${var.project}-shared-${var.policy_general_dev_ecr}"
  path = "/"
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Sid" : "AllowPushingToECR",
        "Effect" : "Allow",
        "Action" : [
          "ecr:BatchCheckLayerAvailability",
          "ecr:BatchGetImage",
          "ecr:CompleteLayerUpload",
          "ecr:GetDownloadUrlForLayer",
          "ecr:InitiateLayerUpload",
          "ecr:PutImage",
          "ecr:UploadLayerPart"
        ],
        "Resource" : [
          "arn:aws:ecr:eu-central-1:*:repository/dgtmon-*"
        ]
      },
      {
        "Action" : [
          "ecr:GetAuthorizationToken"
        ],
        "Effect" : "Allow",
        "Resource" : "*"
      }
    ]
  })
}

resource "aws_iam_policy" "dev_apkg_upload" {
  name = "${var.project}-shared-${var.policy_general_dev_apkg_upload}"
  path = "/"
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Sid" : "AllowUploadingManuscriptsToS3",
        "Effect" : "Allow",
        "Action" : [
          "s3:ListBucket",
          "s3:*Object"
        ],
        "Resource" : [
          "arn:aws:s3:::dgtmon-*-apkg-upload/*",
          "arn:aws:s3:::dgtmon-*-apkg-upload"
        ]
      }
    ]
  })
}

resource "aws_iam_group_policy_attachment" "dev_ecr" {
  group      = aws_iam_group.devs.name
  policy_arn = aws_iam_policy.dev_ecr.arn
}

resource "aws_iam_group_policy_attachment" "dev_apkg_upload" {
  group      = aws_iam_group.devs.name
  policy_arn = aws_iam_policy.dev_apkg_upload.arn
}

resource "aws_iam_user" "cli_PAK" {
  name = "${var.project}-shared-${var.usr_cli_PAK}"
}

resource "aws_iam_user_group_membership" "cli_PAK" {
  user = aws_iam_user.cli_PAK.name
  groups = [
    aws_iam_group.devs.name,
  ]
}

resource "aws_iam_access_key" "cli_PAK" {
  user = aws_iam_user.cli_PAK.name
}

output "cli_PAK_access_key_id" {
  value       = aws_iam_access_key.cli_PAK.id
  description = "The access key ID for the CLI PAK user. Add the access key and secret access key retrieved by an admin to your AWS CLI config file."
}
