terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = "us-east-2"
}

# Raw S3 bucket

resource "aws_s3_bucket" "raw_data_bucket" {
  bucket = "raw-news-api-data"

  tags = {
    Name        = "Raw Data"
    Environment = "Dev"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "raw_data_bucket_lc" {
  bucket = aws_s3_bucket.raw_data_bucket.id

  rule {
    id = "rule-1"

    filter {}

    expiration {
      days = 7
    }

    status = "Enabled"
  }
}

# Enriched S3 bucket

resource "aws_s3_bucket" "enriched_news" {
  bucket = "enriched-nlp-news-data"

  tags = {
    Name        = "Data enriched with NLP and validated"
    Environment = "Dev"
  }
}


resource "aws_s3_bucket_lifecycle_configuration" "enriched_data_bucket_lc" {
  bucket = aws_s3_bucket.enriched_news.id

  rule {
    id = "rule-1"

    filter {}

    expiration {
      days = 7
    }

    status = "Enabled"
  }
}

# News Ingestion EventBridge Scheduler

resource "aws_scheduler_schedule" "trigger_news_ingest" {
    name       = "trigger-news-ingest"
    group_name = "default"

    flexible_time_window {
        mode = "OFF"
    }

    schedule_expression = "cron(0 9,16 * * ? *)"

    schedule_expression_timezone =  "America/New_York"
    
    target {
        arn = 
        role_arn = 
    }
}