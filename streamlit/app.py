import streamlit as st
import duckdb
from dotenv import load_dotenv
import os

load_dotenv()

BUCKET = "news-nl-enriched"
REGION = "us-east-2"
KEY = "*.parquet"
S3_URI = f"s3://{BUCKET}/{KEY}"

AWS_ACCESS_KEY=os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY=os.getenv("AWS_SECRET_ACCESS_KEY")


q=f"""
CREATE OR REPLACE SECRET secret (
    TYPE s3,
    PROVIDER config,
    KEY_ID {AWS_ACCESS_KEY},
    SECRET {AWS_SECRET_ACCESS_KEY},
    REGION 'us-east-2',
    ENDPOINT 's3.{REGION}.amazonaws.com'
);
"""

duckdb.sql("INSTALL httpfs; LOAD httpfs;")
duckdb.sql(q)

def load_data():
    query = f"SELECT * FROM '{S3_URI}'"
    return duckdb.sql(query).df()

df = load_data()
st.subheader("Aggregated Sentiment View")
st.dataframe(df)