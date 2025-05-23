terraform {
  backend "s3" {
    bucket         = "dgtmon-shared-s3-tfstate-backend"
    dynamodb_table = "dgtmon-shared-dyndb-tfstate-locktbl"
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
