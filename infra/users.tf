resource "aws_iam_group" "devs" {
  name = "${var.project}-${var.env}-${var.group_devs}"
  path = "/users/"
}

resource "aws_iam_group" "sysadmins" {
  name = "${var.project}-${var.env}-${var.group_sysadmins}"
  path = "/users/"
}

resource "aws_iam_policy" "dev_ecr" {
  name = "${var.project}-${var.env}-${var.policy_general_dev_ecr}"
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
  name = "${var.project}-${var.env}-${var.policy_general_dev_apkg_upload}"
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

resource "aws_iam_policy" "sysadmins_vm_connect" {
  name = "${var.project}-${var.env}-${var.policy_sysadmins_vm_connect}"
  path = "/"
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Sid" : "AllowStartSessionToWebServer",
        "Effect" : "Allow",
        "Action" : [
          "ssm:StartSession"
        ],
        "Resource" : [
          aws_instance.websvr.arn,
          "arn:aws:ssm:*:*:document/SSM-SessionManagerRunShell",
          "arn:aws:ssm:*:*:document/AWS-StartSSHSession"
        ]
      },
      {
        "Sid" : "AllowManageOwnSessions",
        "Effect" : "Allow",
        "Action" : [
          "ssm:ResumeSession",
          "ssm:TerminateSession"
        ],
        "Resource" : [
          "arn:aws:ssm:*:*:session/$${aws:username}-*"
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

resource "aws_iam_group_policy_attachment" "vm_connect" {
  group      = aws_iam_group.sysadmins.name
  policy_arn = aws_iam_policy.sysadmins_vm_connect.arn
}

## Specific users

# For every user remember to create access keys via the console (admin)
# and then add them to the AWS CLI config file (user).

resource "aws_iam_user" "cli_ELG" {
  name = "${var.project}-${var.env}-${var.usr_cli_ELG}"
}

resource "aws_iam_user_group_membership" "cli_ELG" {
  user = aws_iam_user.cli_ELG.name
  groups = [
    aws_iam_group.devs.name,
  ]
}

resource "aws_iam_user" "cli_PAK" {
  name = "${var.project}-${var.env}-${var.usr_cli_PAK}"
}

resource "aws_iam_user_group_membership" "cli_PAK" {
  user = aws_iam_user.cli_PAK.name
  groups = [
    aws_iam_group.devs.name,
    aws_iam_group.sysadmins.name,
  ]
}

# resource "aws_iam_user_policy" "cli_PAK_ssm_websvr" {
#   name = "${var.project}-${var.env}-cli-pak-ssm-websvr"
#   user = aws_iam_user.cli_PAK.name
#   policy = jsonencode({
#     "Version" : "2012-10-17",
#     "Statement" : [
#       {
#         "Sid" : "AllowStartSessionToWebServer",
#         "Effect" : "Allow",
#         "Action" : [
#           "ssm:StartSession"
#         ],
#         "Resource" : [
#           aws_instance.websvr.arn,
#           "arn:aws:ssm:*:*:document/SSM-SessionManagerRunShell",
#           "arn:aws:ssm:*:*:document/AWS-StartSSHSession"
#         ]
#       },
#       {
#         "Sid" : "AllowManageOwnSessions",
#         "Effect" : "Allow",
#         "Action" : [
#           "ssm:ResumeSession",
#           "ssm:TerminateSession"
#         ],
#         "Resource" : [
#           "arn:aws:ssm:*:*:session/$${aws:username}-*"
#         ]
#       },
#       {
#         "Sid" : "AllowSessionDiscovery",
#         "Effect" : "Allow",
#         "Action" : [
#           "ec2:DescribeInstances",
#           "ssm:DescribeInstanceInformation",
#           "ssm:DescribeSessions",
#           "ssm:GetConnectionStatus"
#         ],
#         "Resource" : "*"
#       }
#     ]
#   })
# }

