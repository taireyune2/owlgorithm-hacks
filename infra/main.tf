terraform {
  required_version = ">= 0.12"
  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "~> 5.27"
    }
  }

  backend "s3" {
    bucket = "keypointvision.infrastructure.terraform"
    key = "owlspeak/terraform.tfstate"
    region = "us-west-2"
    encrypt = true
    dynamodb_table = "keypointvision.infrastructure"
  }
}

provider "aws" {
  region = var.region
}

data "terraform_remote_state" "base" {
  backend = "s3"
  config = {
    bucket = "keypointvision.infrastructure.terraform"
    key = "base/terraform.tfstate"
    region = var.region
  }
}

data "terraform_remote_state" "main" {
  backend = "s3"
  config = {
    bucket = "keypointvision.infrastructure.terraform"
    key = "portfolio/terraform.tfstate"
    region = var.region
  }
}

resource "aws_lb_listener_certificate" "main" {
  listener_arn = data.terraform_remote_state.main.outputs.aws_lb_main_listener_arn
  certificate_arn = var.certificate_arn
}

