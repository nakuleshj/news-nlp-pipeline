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
resource "aws_lambda_permission" "allow_s3_invoke" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.enrich_news.arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.raw_data_bucket.arn
}

resource "aws_s3_bucket_notification" "raw_news_writes" {
  bucket = aws_s3_bucket.raw_data_bucket.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.enrich_news.arn
    events = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_lambda_permission.allow_s3_invoke]
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

data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}


data "aws_iam_policy_document" "lambda_execution_policy" {
  statement {
    sid    = "VisualEditor0"
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue"
    ]
    resources = [
      "arn:aws:secretsmanager:us-east-2:860131551212:secret:news_api-*"
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["*"]
  }

  statement {
    effect = "Allow"
    actions = [
      "s3:*",
      "s3-object-lambda:*"
    ]
    resources = ["*"]
  }
}


resource "aws_iam_role" "ud_lambda_execution_role" {
  name               = "ud-lambda-execution-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

resource "aws_iam_role_policy" "inline_policy" {
  role = aws_iam_role.ud_lambda_execution_role.id
  policy = data.aws_iam_policy_document.lambda_execution_policy.json
  
}

resource "aws_lambda_function" "ingest_news" {
  filename      = "./lambda_scripts/news_ingest/ingest_news.zip"
  function_name = "ingest_news"
  role          = aws_iam_role.ud_lambda_execution_role.arn
  handler       = "ingest_news.lambda_handler"

  runtime = "python3.13"

  timeout = 30

  memory_size = 256

  layers = [aws_lambda_layer_version.requests_layer.arn]

  tags = {
    Environment = "production"
    Application = "news-pipeline"
  }
}

resource "aws_lambda_function" "enrich_news" {

  filename      = "./lambda_scripts/enrich_raw_data/enrich_raw_data.zip"
  function_name = "enrich_raw_data"
  role          = aws_iam_role.ud_lambda_execution_role.arn
  handler       = "enrich_raw_data.lambda_handler"

  runtime = "python3.13"

  timeout = 30

  layers = [
    aws_lambda_layer_version.nltk_layer.arn,
    aws_lambda_layer_version.pandas_layer.arn
  ]

  tags = {
    Environment = "production"
    Application = "news-pipeline"
  }
}

resource "aws_lambda_layer_version" "requests_layer" {

  layer_name = "requests_layer"
  filename   = "./layers/requests_layer.zip"

  compatible_runtimes = ["python3.13"]
}

resource "aws_lambda_layer_version" "nltk_layer" {

  layer_name = "nltk_layer"
  filename   = "./layers/nltk_layer.zip"

  compatible_runtimes = ["python3.13"]
}

resource "aws_lambda_layer_version" "pandas_layer" {

  layer_name = "pandas_layer"
  filename   = "./layers/pandas_layer.zip"

  compatible_runtimes = ["python3.13"]
}

# News Ingestion EventBridge Scheduler
resource "aws_iam_role" "scheduler_role" {
  name = "eventbridge-scheduler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "scheduler.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "scheduler_lambda_attachment" {
  role       = aws_iam_role.scheduler_role.name
  policy_arn = "arn:aws:iam::aws:policy/AWSLambda_FullAccess"
}

resource "aws_scheduler_schedule" "trigger_news_ingest" {
    name       = "trigger-news-ingest"
    group_name = "default"

    flexible_time_window {
        mode = "OFF"
    }

    schedule_expression = "cron(0 9,16 * * ? *)"

    schedule_expression_timezone =  "America/New_York"
    
    target {
        arn = aws_lambda_function.ingest_news.arn
        role_arn = aws_iam_role.scheduler_role.arn
    }
}