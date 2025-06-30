terraform {
  backend "s3" {
    bucket         = "TFSTATE_BACKEND"
    dynamodb_table = "TFSTATE_LOCKTBL"
    encrypt        = true
    profile        = "oidc"
  }
}

provider "aws" {
  profile = "oidc"
  region  = var.region
  default_tags {
    tags = {
      org     = var.org
      project = var.project
    }
  }
}
