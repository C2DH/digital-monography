## Set by the DevOps team

variable "assume_role_arn" {
  type        = string
  description = "ARN of the role to leverage the CI role in AWS"
  default     = "arn:aws:iam::000000000000:role/Just-A-Placeholder"
}

variable "assume_role_external_id" {
  type        = string
  description = "External Reference for assumed role"
  default     = "cicd-admin"
}

variable "project_name" {
  type        = string
  description = "Global Name of the project"
  default     = "Another AWSome Project"
}

variable "region" {
  type        = string
  description = "AWS Region of the project"
  default     = "eu-central-1"
}

variable "environment" {
  type        = string
  description = "Environment/Branch of the Project"
}

variable "aws_account_environment" {
  type        = string
  description = "The AWS Account we're working with, e.g. DELIVERY or ITSM"
}

## Set by the Dev team

variable "staticws_wip_bucket_name" {
  type        = string
  description = "Name of the bucket to which static website will be exported. E.g. domain_name."
}

variable "ir_apkg_md_bucket_name" {
  type        = string
  description = "Name of the bucket for intermediate format when transforming .html into .md"
}

variable "upload_apkg_bucket_name" {
  type        = string
  description = "Name of the bucket for uploading authors' packages (apkg) to AWS cloud."
}

variable "api_gateway_api_key" {
  type        = string
  description = "API key used for cloud-to-cloud communication with the API Gateway"
  validation {
    condition     = length(var.api_gateway_api_key) >= 20 && length(var.api_gateway_api_key) < 128 && can(regex("^[0-9A-Za-z]+$", var.api_gateway_api_key))
    error_message = "The api key must be an alphanumeric string of length between 20 and 128"
  }
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
