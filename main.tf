terraform {
  backend "s3" {
    bucket         = "gitlabtfaws-tfstate"
    key            = "statefile.tfstate"
    dynamodb_table = "gitlabtfaws-state-lock-table"
    encrypt        = true
    profile        = "oidc"
  }
}

provider "aws" {
  profile = "oidc"
  region  = var.region
}
