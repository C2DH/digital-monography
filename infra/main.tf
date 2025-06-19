terraform {
  backend "s3" {
    bucket         = "825580929289"
    dynamodb_table = ""
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
