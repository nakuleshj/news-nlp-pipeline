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

# Scripts bucket

resource "aws_s3_bucket" "lambda_scripts" {
  bucket = "news-pipeline-lambda-scripts"

  tags = {
    Name        = "Lambda Scripts"
    Environment = "Dev"
  }
}

data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
  statement {
    sid="VisualEditor0"
    effect = "Allow"
    actions = [
        "secretsmanager:GetSecretValue"
    ]
    resources = [
        "arn:aws:secretsmanager:us-east-2:860131551212:secret:news_api-*"
    ]
  }
  statement {
    effect= "Allow"
    actions = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
    ]
    resources = [
        "*"
    ]
  }
  statement {
    effect = "Allow"
    actions = [
                "s3:*",
                "s3-object-lambda:*"
            ]
    resources = [
        "*"
        ]
  }
}

resource "aws_iam_role" "ingest_lambda_execution_role" {
    name               = "ingest_lambda-execution-role"
    assume_role_policy = data.aws_iam_policy_document.assume_role.json

}

resource "aws_lambda_function" "ingest_news" {
    s3_bucket = aws_s3_bucket.lambda_scripts.bucket
    s3_key = "ingest_news.zip"
    function_name    = "ingest_news"
    role             = aws_iam_role.ingest_lambda_execution_role.arn
    handler          = "ingest_news.lambda_handler"

    runtime = "python3.13"

    tags = {
        Environment = "production"
        Application = "news-pipeline"
    }
}

# News Ingestion EventBridge Scheduler

/*resource "aws_scheduler_schedule" "trigger_news_ingest" {
    name       = "trigger-news-ingest"
    group_name = "default"

    flexible_time_window {
        mode = "OFF"
    }

    schedule_expression = "cron(0 9,16 * * ? *)"

    schedule_expression_timezone =  "America/New_York"
    
    target {
        arn = aws_lambda_function.ingest_news.arn
        role_arn = 
    }
}*/

resource "aws_lambda_layer_version" "pandas" {
  s3_bucket = aws_s3_object.lambda_layer_zip.bucket
  s3_key    = aws_s3_object.lambda_layer_zip.key

  layer_name = "lambda_layer_name"

  compatible_runtimes      = ["nodejs20.x", "python3.12"]
  compatible_architectures = ["x86_64", "arm64"]
}
resource "aws_lambda_layer_version" "requests" {
  s3_bucket = aws_s3_object.lambda_layer_zip.bucket
  s3_key    = aws_s3_object.lambda_layer_zip.key

  layer_name = "lambda_layer_name"

  compatible_runtimes      = ["nodejs20.x", "python3.12"]
  compatible_architectures = ["x86_64", "arm64"]
}
resource "aws_lambda_layer_version" "nltk" {
  s3_bucket = aws_s3_object.lambda_layer_zip.bucket
  s3_key    = aws_s3_object.lambda_layer_zip.key

  layer_name = "lambda_layer_name"

  compatible_runtimes      = ["nodejs20.x", "python3.12"]
  compatible_architectures = ["x86_64", "arm64"]
}
