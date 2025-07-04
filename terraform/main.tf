terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0.0" # or the version you're using
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

module "s3" {
  source = "./modules/s3"
}