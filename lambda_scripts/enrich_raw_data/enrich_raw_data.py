import json
import boto3
import pandas as pd
from io import BytesIO
import os, sys, logging
from dq_check import validate_dataframe

logging.basicConfig(level=logging.INFO)

sys.path.append("/opt")
os.environ["NLTK_DATA"] = "/opt/python/nltk_data"
print("Files in /opt:", os.listdir("/opt"))
print("Files in /opt/python/nltk_data:", os.listdir("/opt/python/nltk_data"))
print("NLTK_DATA path:", os.environ.get("NLTK_DATA"))

from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Load NLP tools
analyzer = SentimentIntensityAnalyzer()

def get_sentiment_score(text):
    return analyzer.polarity_scores(text)["compound"]

def get_sentiment(score):
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
    
    df = df[["publishedAt", "title", "source.name","url","description"]].rename(
        columns={"publishedAt": "published_at", "source.name": "source"}
    )
    df.drop_duplicates(subset=["title"], inplace=True)
    df.dropna(subset=["description"], inplace=True)

    df["sentiment_score"] = df["description"].apply(get_sentiment_score)
    df["sentiment"] = df["sentiment_score"].apply(get_sentiment)
    df["published_at"] = pd.to_datetime(df["published_at"])
    try:
        validate_dataframe(df)
        logging.info("Validation successful.")
    except AssertionError as e:
        logging.error(f"Validation error: {e}")

    buffer = BytesIO()
    df.to_parquet(buffer, index=False, engine="fastparquet")
    buffer.seek(0)

    output_key = f"{key.split('/')[-1].replace('.json', '.parquet')}"
    s3.put_object(
        Bucket="news-nl-enriched",
        Key=output_key,
        Body=buffer.getvalue(),
        ContentType="application/octet-stream"
    )
    
    print(f"Saved enriched file to: {output_key}")
    return {
        "statusCode": 200,
        "message": f"Saved: {output_key}"
    }