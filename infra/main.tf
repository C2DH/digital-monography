terraform {
  backend "s3" {
    bucket         = "${var.project}-shared-s3-tfstate-backend"
    dynamodb_table = "${var.project}-shared-dyndb-tfstatelock-tbl"
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
