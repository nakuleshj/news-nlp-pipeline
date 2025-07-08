import streamlit as st
import duckdb
from dotenv import load_dotenv
import os
import plotly.graph_objects as go
import numpy as np

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

@st.cache_data(ttl=3600) # Cache data for 1 hour
def load_data():
    query = f"SELECT * FROM '{S3_URI}'"
    return duckdb.sql(query).df()

def sentiment_guage_chart(avg_sentiment):
    fig = go.Figure(go.Indicator(
    mode = "gauge",
    value=avg_sentiment,
    gauge={
        'axis':{
            'range':[-1, 1],
        },
        'steps':[
            {'range':[-1,-0.3],'color':'red','name':'Negative'},
            {'range':[-0.3,0.3],'color':'yellow'},
            {'range':[0.3,1],'color':'green'}
        ],
        "threshold":{
            "line":{
                "color":"black",
                "width": 2
            },
            "value":avg_sentiment,
            "thickness": 1
        },
        "bar": {
            "thickness": 0
        }
    },
    domain = {'x': [0, 1], 'y': [0, 1]},
    title = {'text': "Sentiment Score"}))
    return fig
    
df = load_data()

st.set_page_config(page_title="NewsPulse Dashboard", layout="wide")
st.title("Aggregated News Dashboard")

st.header("Summary")

avg_sentiment_score=duckdb.query("SELECT AVG(sentiment_score) FROM df").to_df().values[0][0].round(2)

st.plotly_chart(sentiment_guage_chart(avg_sentiment_score))
col1, col2, col3=st.columns(3)
with col1:
    n_articles=duckdb.query("SELECT COUNT(*) from df;").to_df().values[0][0].round(0)
    st.metric("Total Articles", n_articles, border=True)
with col2:
    n_sources=duckdb.query("SELECT COUNT(DISTINCT source) from df;").to_df().values[0][0].round(0)
    st.metric("Unique Sources", n_sources, border=True)

st.subheader("Recent Positive News")
positive=duckdb.query("SELECT * FROM df WHERE sentiment='positive' ORDER BY published_at DESC LIMIT 5;").to_df()
st.dataframe(positive)

st.subheader("Recent Negative News")
negative=duckdb.query("SELECT * FROM df WHERE sentiment='negative' ORDER BY published_at DESC LIMIT 5;").to_df()
st.dataframe(negative)

st.subheader("Sentiment Heatmap by News Source")
news_sources=duckdb.query("""
                          SELECT source,
                          COUNT(CASE WHEN sentiment_score > 0 THEN 1 ELSE NULL END) AS Positive,
                          COUNT(CASE WHEN sentiment_score = 0 THEN 1 ELSE NULL END) AS Neutral,
                          COUNT(CASE WHEN sentiment_score < 0 THEN 1 ELSE NULL END) AS Negative
                          FROM df
                          GROUP BY source;
                          """).to_df().set_index("source")

st.dataframe(news_sources)