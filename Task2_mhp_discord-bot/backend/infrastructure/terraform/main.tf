terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
  }

  # Remote state backend — uncomment and configure for Jenkins use.
   backend "s3" {
     bucket         = "trainee-2026-niloy-mhp-tfstate"
     key            = "mhp-backend/terraform.tfstate"
     region         = "ap-south-1"
     dynamodb_table = "trainee-2026-niloy-mhp-tflock"
     encrypt        = true
   }
}

provider "aws" {
  region = var.aws_region
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
