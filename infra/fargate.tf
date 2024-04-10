# //Create a role with necessary policy to access S3 bucket
resource "aws_iam_role" "assume_fargate_role" {
  name               = "dgtmon-uploads-events"
  assume_role_policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": "events.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
POLICY
}

resource "aws_iam_role_policy" "ecs_events_run_task_with_any_role" {
  name   = "myproject-uploads-run-task-with-any-role"
  role   = aws_iam_role.assume_fargate_role.id
  policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "ecs:RunTask",
      "Resource": "${replace(aws_ecs_task_definition.task_def.arn, "/:\\d+$/", ":*")}"
    }
  ]
}
POLICY
}

resource "aws_iam_role_policy_attachment" "attach_s3_policy" {
  role       = aws_iam_role.assume_fargate_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "attach_ecstaskexec_policy" {
  role       = aws_iam_role.assume_fargate_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_cloudwatch_event_rule" "uploads" {
  name          = "upload_invokes_ecs_fargate_task"
  description   = "Capture S3 events on uploads bucket"
  event_pattern = <<PATTERN
{
  "source": [
    "aws.s3"
  ],
  "detail": {
    "eventSource": [
      "s3.amazonaws.com"
    ],
    "eventName": [
      "PutObject",
      "CompleteMultipartUpload"
    ],
    "requestParameters": {
      "bucketName": [
        "${aws_s3_bucket.upload_apkg.id}"
      ]
    }
  }
}
PATTERN
}

resource "aws_ecs_task_definition" "task_def" {
  family                   = "sample-task-definition"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.assume_fargate_role.arn # TODO: maybe split?
  task_role_arn            = aws_iam_role.assume_fargate_role.arn # TODO: maybe split?

  container_definitions = <<DEFINITION
  [
    {
      "name": "sample-container",
      "image": "ghcr.io/kaminski-pawel/ecs-task-example:latest",
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-region": "eu-central-1",
          "awslogs-group": "${data.aws_cloudwatch_log_group.general_purpose_logs.name}",
          "awslogs-stream-prefix": "ecs_task"
        }
      },
      "environment": [
        {
          "name": "bucketName",
          "value": "${var.staticws_wip_bucket_name}"
        }
      ]
    }
  ]
  DEFINITION
}

resource "aws_cloudwatch_event_target" "uploads" {
  target_id = "myproject-process-uploads"
  arn       = aws_ecs_cluster.ecs_cluster.arn
  rule      = aws_cloudwatch_event_rule.uploads.name
  role_arn  = aws_iam_role.assume_fargate_role.arn
  ecs_target {
    launch_type         = "FARGATE"
    task_count          = 1
    task_definition_arn = aws_ecs_task_definition.task_def.arn
    network_configuration {
      security_groups = [aws_security_group.efs_access_sg.id]
      subnets         = aws_subnet.efs_public[*].id
      # subnets = aws_subnet.efs_public[0].id # this would create a task only in the first subnet
      assign_public_ip = false
    }
  }
  input_transformer {
    input_paths = {
      s3_bucket = "$.detail.requestParameters.bucketName"
      s3_key    = "$.detail.requestParameters.key"
    }
    input_template = <<TEMPLATE
{
  "containerOverrides": [
    {
      "name": "myproject-task",
      "environment": [
        { "name": "S3_BUCKET", "value": <s3_bucket> },
        { "name": "S3_KEY", "value": <s3_key> }
      ]
    }
  ]
}
    TEMPLATE
  }
}

resource "aws_ecs_cluster" "ecs_cluster" {
  name = "dgtmon_ecs_cluster"
}

# # resource "aws_security_group" "fargate_sg" {
# #   name        = "fargate_sg"
# #   description = "Security Group for Fargate"
# #   vpc_id      = aws_vpc.dgtmon_vpc.id
# #   ingress {
# #     from_port   = 2049
# #     to_port     = 2049
# #     protocol    = "tcp"
# #     cidr_blocks = ["0.0.0.0/0"]
# #   }
# #   egress {
# #     from_port   = 0
# #     to_port     = 0
# #     protocol    = "-1"
# #     cidr_blocks = ["0.0.0.0/0"]
# #   }
# # }
