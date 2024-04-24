terraform {
  backend "s3" {
    bucket         = "dgtmon-tfstate-backend"
    key            = "statefile.tfstate"
    dynamodb_table = "dgtmon-state-lock-table"
    encrypt        = true
    profile        = "oidc"
  }
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0.1"
    }
  }
}

provider "aws" {
  profile = "oidc"
  region  = var.region
}

provider "docker" {}
