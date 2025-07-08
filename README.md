# Event-Driven Serverless Pipeline for Real-Time News NLP and Sentiment Scoring

A fully serverless, event-driven data pipeline that ingests, enriches, validates, and visualizes real-time news data using AWS services. Designed for cost-efficient, scalable deployment using only free-tier AWS services.

***Live Dashboard (Deployed on Streamlit Cloud):*** [https://your-streamlit-url.com](https://your-streamlit-url.com)

***GitHub Repository:*** [https://github.com/nakuleshj/news-nlp-pipeline](https://github.com/nakuleshj/news-nlp-pipeline)

## Problem Statement
News data is critical for monitoring sentiment shifts across industries and companies. However, traditional pipelines are batch-heavy, costly, or not scalable. This project solves that by providing a **real-time, serverless architecture** to process news with **NLP sentiment scoring** and expose it via a low-latency, self-service dashboard.

## Features

- **Scheduled ingestion** at 9AM and 5PM using EventBridge
- **NLP scoring** using VADER for sentiment scoring & classification
- **Data quality validation** with Python & pandas library
- **Lightweight querying** with DuckDB
- **Interactive Streamlit dashboard** with sentiment gauge, sentiment heatmaps, source analysis, and refresh button
- **Dashboard deployed on Streamlit Cloud** for easy sharing and low-latency access
- **Fully Free-Tier Deployable**

## Tech Stack

**Cloud & Infrastructure:** AWS Lambda · S3 · EventBridge · Streamlit Cloud  
**Data Processing:** Python · pandas · VADER · boto3
**Storage Formats:** JSON (raw data), Parquet (enriched data)
**Query Engine**: DuckDB  
**Dashboarding & Visualization:** Streamlit  

## Components

| Layer            | Technology                 | Description |
|------------------|----------------------------|-------------|
| **Data Source**   | [News API](https://newsapi.org) | Provides real-time news articles for ingestion |
| **Ingestion**     | AWS Lambda + EventBridge   | Triggers news ingestion at 9AM/5PM daily |
| **Storage**       | Amazon S3                  | Stores raw JSON (Bronze) and enriched Parquet (Silver) |
| **Processing**    | AWS Lambda + VADER         | Performs sentiment scoring and data transformation |
| **Validation**    | Python (pandas)            | Applies custom validation: schema checks, null filtering, sentiment score ranges |
| **Query Layer**   | DuckDB                     | Runs SQL queries directly on Parquet files in S3 |
| **Visualization** | Streamlit                  | Displays sentiment scores, trends, and manual reloads |

## Architecture Flow (Step-by-Step)

![NewsPulse Architecture](./assets/updated-news-pipeline.png)

1. **News Ingestion**  
   EventBridge triggers a Lambda function twice daily to fetch news from NewsAPI, storing the raw JSON in an S3 `raw` bucket.

2. **Event-Driven Enrichment**  
   An S3 Event Notification invokes a second Lambda that:
   - Parses and enriches the data with NLP sentiment scores
   - Applies `pandas`-based validation
   - Writes the result as Parquet to a separate S3 `enriched` bucket 

3. **Querying & Visualization**  
   - DuckDB queries the Parquet files directly from S3 (no database needed)
   - Streamlit dashboard displays sentiment scores, source breakdowns through interactive visualizations


## Key Learnings
- Designed a cost-efficient, production-grade serverless pipeline
- Leveraged event-driven architecture with AWS-native tools
- Applied custom data quality monitoring with `pandas`-based validation 
- Built a real-time dashboard to visualize sentiment insights with reload triggers


## Future Improvements
- Add topic modeling (e.g., LDA) or named entity extraction
- Integrate with Amazon Athena or Redshift Spectrum for large-scale analytics
- Add Slack/email alerting for negative sentiment spikes
- Implement full CI/CD pipeline (GitHub Actions + Terraform)

