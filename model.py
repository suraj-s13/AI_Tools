import os
import re
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


DATASET_PATH = os.path.join(os.path.dirname(__file__), "dataset", "ai_tools.csv")
FEEDBACK_PATH = os.path.join(os.path.dirname(__file__), "feedback", "feedback.csv")

# Global model state
_vectorizer = None
_tfidf_matrix = None
_df = None
_tool_weights = {}


def preprocess_text(text: str) -> str:
    """Lowercase, strip punctuation, and normalize whitespace."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def load_dataset() -> pd.DataFrame:
    """Load the AI tools CSV dataset."""
    df = pd.read_csv(DATASET_PATH)
    df = df.fillna("")
    # Create a combined text field for TF-IDF
    df["combined_text"] = (
        df["tool_name"].apply(preprocess_text) + " "
        + df["category"].apply(preprocess_text) + " "
        + df["description"].apply(preprocess_text) + " "
        + df["keywords"].apply(preprocess_text)
    )
    return df


def build_feedback_weights() -> dict:
    weights = {}
    if not os.path.exists(FEEDBACK_PATH):
        return weights

    try:
        fb = pd.read_csv(FEEDBACK_PATH)
        if fb.empty or "tool_name" not in fb.columns:
            return weights

        for tool, group in fb.groupby("tool_name"):
            pos = (group["feedback"] == "useful").sum()
            neg = (group["feedback"] == "not_useful").sum()
            score = 1.0 + (pos * 0.15) - (neg * 0.10)
            weights[tool] = max(0.1, score)  # never let weight go below 0.1
    except Exception:
        pass

    return weights


def train_model():
    global _vectorizer, _tfidf_matrix, _df, _tool_weights

    _df = load_dataset()
    _tool_weights = build_feedback_weights()

    _vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        min_df=1,
        max_df=0.95,
        sublinear_tf=True,
    )
    _tfidf_matrix = _vectorizer.fit_transform(_df["combined_text"])


def get_recommendations(query: str, top_n: int = 5) -> list[dict]:
    global _vectorizer, _tfidf_matrix, _df, _tool_weights

    # Lazy initialisation
    if _vectorizer is None:
        train_model()

    processed_query = preprocess_text(query)
    query_vec = _vectorizer.transform([processed_query])
    similarities = cosine_similarity(query_vec, _tfidf_matrix).flatten()

    # Apply feedback weights
    weighted_scores = []
    for idx, sim in enumerate(similarities):
        tool = _df.iloc[idx]["tool_name"]
        weight = _tool_weights.get(tool, 1.0)
        weighted_scores.append((idx, sim * weight))

    # Sort descending by weighted score
    weighted_scores.sort(key=lambda x: x[1], reverse=True)
    top_indices = [idx for idx, _ in weighted_scores[:top_n]]
    top_scores = [score for _, score in weighted_scores[:top_n]]

    results = []
    for rank, (idx, score) in enumerate(zip(top_indices, top_scores)):
        row = _df.iloc[idx]
        results.append(
            {
                "tool_name": row["tool_name"],
                "category": row["category"],
                "description": row["description"],
                "icon_url": row["icon_url"],
                "website_link": row["website_link"],
                "score": round(float(score), 4),
                "rank": rank + 1,
            }
        )

    return results
