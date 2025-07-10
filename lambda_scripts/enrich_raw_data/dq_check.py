import pandas as pd

def validate_dataframe(df):
    assert not df.empty, "DataFrame is empty."

    # Check for expected columns
    required_columns = {"published_at", "source", "title", "sentiment_score"}
    missing_cols = required_columns - set(df.columns)
    assert not missing_cols, f"Missing columns: {missing_cols}"

    # Data type checks
    assert pd.api.types.is_datetime64_any_dtype(df["published_at"]), "published_at must be datetime"
    assert pd.api.types.is_numeric_dtype(df["sentiment_score"]), "sentiment_score must be numeric"

    # Null checks
    assert df["published_at"].notna().all(), "published_at column has nulls"
    assert df["sentiment_score"].notna().all(), "sentiment_score column has nulls"

    # Sentiment score range checks
    assert df["sentiment_score"].between(-1, 1).all(), "sentiment_score out of expected range"

    # Check for duplicate titles
    assert df["title"].is_unique, "Duplicate titles found"

    return True