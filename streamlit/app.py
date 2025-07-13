import streamlit as st
import duckdb
from dotenv import load_dotenv
import os
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import pandas as pd

load_dotenv()

BUCKET = "enriched-nlp-news-data"
REGION = "us-east-2"
KEY = "*.parquet"
S3_URI = f"s3://{BUCKET}/{KEY}"

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")


q = f"""
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


@st.cache_data(ttl=3600)  # Cache data for 1 hour
def load_data():
    query = f"SELECT * FROM '{S3_URI}'"
    return duckdb.sql(query).df()


def sentiment_emoji(score):
    if score > 0.3:
        return "🟢 😊 Positive"
    elif score < -0.3:
        return "🔴 😠 Negative"
    else:
        return "🟡 😐 Neutral"


def plot_sentiment_heatmap(data):

    fig, ax = plt.subplots()
    sns.heatmap(data, annot=True, fmt=".0f", cmap="coolwarm", ax=ax)
    ax.set_ylabel("News Source")
    ax.set_xlabel("Sentiment")
    return fig


def plot_wordcloud(df):
    text = " ".join(df["title"].dropna())
    wordcloud = WordCloud(width=800, height=500, background_color="white").generate(
        text
    )
    fig, ax = plt.subplots()
    ax.imshow(wordcloud, interpolation="bilinear")
    ax.set_axis_off()
    return fig


df = load_data()

st.set_page_config(page_title="Economic News Dashboard", layout="wide")
st.title("Economic News Dashboard")

st.subheader("Summary")


col1, col2, col3 = st.columns(3)
with col1:
    n_articles = duckdb.query("SELECT COUNT(*) from df;").to_df().values[0][0].round(0)
    st.metric("Total Articles", n_articles, border=True)
with col2:
    n_sources = (
        duckdb.query("SELECT COUNT(DISTINCT source) from df;")
        .to_df()
        .values[0][0]
        .round(0)
    )
    st.metric("Unique Sources", n_sources, border=True)
with col3:
    avg_score = duckdb.query("SELECT avg(sentiment_score) as avg FROM df;").to_df()[
        "avg"
    ][0]
    st.metric("Overall Sentiment", sentiment_emoji(avg_score), border=True)

cols = st.columns(2, vertical_alignment="center")
with cols[0]:
    st.subheader("Sentiment Heatmap by News Source")
    news_sources = (
        duckdb.query(
            """
                          SELECT source,
                          COUNT(CASE WHEN sentiment_score > 0 THEN 1 ELSE NULL END) AS Positive,
                          COUNT(CASE WHEN sentiment_score = 0 THEN 1 ELSE NULL END) AS Neutral,
                          COUNT(CASE WHEN sentiment_score < 0 THEN 1 ELSE NULL END) AS Negative
                          FROM df
                          GROUP BY source
                          ORDER BY COUNT(*) DESC
                          LIMIT 10;
                          """
        )
        .to_df()
        .set_index("source")
    )
    st.pyplot(plot_sentiment_heatmap(news_sources))
with cols[1]:
    st.subheader("Word Cloud of News Headlines")
    st.pyplot(plot_wordcloud(df))

st.subheader("Recent News by Sentiment")
tab_names = ["Positive", "Neutral", "Negative"]
recent_news_tabs = st.tabs(tab_names)
recent_news_dfs = [pd.DataFrame(), pd.DataFrame(), pd.DataFrame()]

for i in range(len(recent_news_dfs)):
    with recent_news_tabs[i]:
        recent_news_dfs[i] = duckdb.query(
            f"SELECT title, url, source, description, published_at, round(sentiment_score,2) as score FROM df WHERE sentiment LIKE '{tab_names[i].lower()}' ORDER BY published_at DESC LIMIT 5;"
        ).to_df()
        for index, row in recent_news_dfs[i].iterrows():
            st.markdown(f"#### [{row['title']}]({row['url']})")
            st.write(f"**Source**: {row['source']}")
            st.write(f"**Description**: {row['description']}")
            st.write(f"**Date**: {row['published_at'].strftime('%Y-%m-%d')}")
            st.write("**Sentiment Score**", row["score"])
            st.markdown("---")
