import json
import boto3
import pandas as pd
from io import BytesIO
import os
import sys

sys.path.append("/opt")
os.environ["NLTK_DATA"] = "/opt/nltk_data"

from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Load NLP tools
analyzer = SentimentIntensityAnalyzer()

def get_sentiment(text):
    if not text:
        return "neutral"
    score = analyzer.polarity_scores(text)["compound"]
    if score >= 0.3:
        return "positive"
    elif score <= -0.3:
        return "negative"
    else:
        return "neutral"

def lambda_handler(event, context):
    s3 = boto3.client("s3")

    # Get event data
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = event["Records"][0]["s3"]["object"]["key"]
    print(f"Triggered by: {bucket}/{key}")

    response = s3.get_object(Bucket=bucket, Key=key)
    raw_data = json.loads(response["Body"].read())

    df = pd.json_normalize(raw_data)
    df = df[["publishedAt", "title", "source.name"]].rename(
        columns={"publishedAt": "timestamp", "source.name": "source"}
    )

    df["sentiment"] = df["title"].apply(get_sentiment)

    buffer = BytesIO()
    df.to_parquet(buffer, index=False, engine="fastparquet")
    buffer.seek(0)

    output_key = f"news/enriched/{key.split('/')[-1].replace('.json', '.parquet')}"
    s3.put_object(
        Bucket="newspulse-enriched-data",
        Key=output_key,
        Body=buffer.getvalue(),
        ContentType="application/octet-stream"
    )

    print(f"Saved enriched file to: {output_key}")
    return {
        "statusCode": 200,
        "message": f"Saved: {output_key}"
    }
