terraform {
  backend "s3" {
    bucket         = "TFSTATE_LOCKTBL"
    dynamodb_table = "TFSTATE_BACKEND"
    encrypt        = true
    profile        = "oidc"
  }
}

provider "aws" {
  profile = "oidc"
  region  = var.region
  default_tags {
    tags = {
      org     = "c2dh"
      project = var.project
    }
  }
}
