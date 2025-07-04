import json, boto3
import requests
from datetime import datetime

def get_news_api_key():
    secrets_client = boto3.client("secretsmanager", region_name="us-east-2")
    secret = secrets_client.get_secret_value(SecretId="news_api")
    return json.loads(secret['SecretString'])["news_api_key"]

def lambda_handler(event, context):
    api_key = get_news_api_key()
    url = f"https://newsapi.org/v2/top-headlines?language=en&apiKey={api_key}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        articles = response.json().get("articles", [])
    except requests.HTTPError as e:
        return {"response":response.status_code,"api_key":api_key, "error": str(e)}
    try:
        s3 = boto3.client("s3")
        now = datetime.now().strftime("%Y-%m-%d-%H-%M")
        key = f"news_{now}.json"
    
        s3.put_object(
            Bucket="raw-data-njk",
            Key=key,
            Body=json.dumps(articles),
            ContentType="application/json"
        )
        print("All Good")
        return {"statusCode": 200, "message": f"{len(articles)} articles saved."}
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"statusCode": 500, "error": str(e)}