variable "project_name" {
  type        = string
  description = "Global Name of the project"
  default     = "Another AWSome Project"
}

variable "region" {
  type        = string
  description = "AWS Region of the project"
  default     = "eu-west-1"
}

variable "environment" {
  type        = string
  description = "Environment/Branch of the Project"
}

## Set by the Dev team

variable "staticws_wip_bucket_name" {
  type        = string
  description = "Name of the bucket to which static website will be exported. E.g. domain_name."
}

variable "ir_apkg_html_bucket_name" {
  type        = string
  description = "Name of the bucket for intermediate format when transforming .docx into .html"
}

variable "ir_apkg_md_bucket_name" {
  type        = string
  description = "Name of the bucket for intermediate format when transforming .html into .md"
}

variable "upload_apkg_bucket_name" {
  type        = string
  description = "Name of the bucket for uploading authors' packages (apkg) to AWS cloud."
}

variable "name" {
  description = "Application Name"
  type        = string
  default     = "sqs-integration"
}

locals {
  description = "Aplication Name"
  app_name    = "${var.name}-${var.environment}"
}

variable "lambda_name" {
  description = "Name for lambda function"
  default     = "lambda"
}

variable "cidr_block" {
  type = string
}

variable "docker_registry_host" {
  type        = string
  description = "Host of the registry where Docker images are located, e.g. organization name for Docker Hub or '<AWS_ACCOUNT_ID>.dkr.ecr.eu-west-1.amazonaws.com' for AWS ECR"
}

variable "builder_img_name" {
  type        = string
  description = "Name of the image for the book builder"
}

variable "preparer_img_name" {
  type        = string
  description = "Name of the image for the preparer"
}

locals {
  versions_data = jsondecode(file("${path.root}/.versions.json"))
}
