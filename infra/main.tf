terraform {
  backend "s3" {
    bucket = "dgtmon-tfstate-backend"
    # key            = "statefile.tfstate"
    dynamodb_table = "dgtmon-state-lock-table"
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
      project = "dgtmon"
      environ = "${var.env}"
    }
  }
}
