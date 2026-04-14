from flask import Flask, render_template, request, jsonify
import json
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

app = Flask(__name__)

# ─── Load Dataset ─────────────────────────────────────────────────────────────
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "ai_tools.json")

def load_tools():
    with open(DATA_PATH, "r") as f:
        return json.load(f)

# ─── Build TF-IDF Model ───────────────────────────────────────────────────────
def build_model(tools):
    """Build TF-IDF vectorizer corpus from tool metadata."""
    corpus = []
    for tool in tools:
        text = " ".join([
            tool["name"],
            tool["category"],
            " ".join(tool["tags"]),
            tool["description"],
            tool["use_cases"],
            tool["pricing"],
            tool["difficulty"]
        ])
        corpus.append(text.lower())
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        stop_words="english",
        max_features=5000
    )
    tfidf_matrix = vectorizer.fit_transform(corpus)
    return vectorizer, tfidf_matrix

tools = load_tools()
vectorizer, tfidf_matrix = build_model(tools)

# ─── LLM-style Keyword Expansion ─────────────────────────────────────────────
KEYWORD_SYNONYMS = {
    "picture": "image photo visual",
    "photo": "image visual photography",
    "draw": "image art illustration",
    "movie": "video film",
    "clip": "video",
    "song": "music audio",
    "voice": "audio speech tts",
    "speak": "audio voice speech",
    "talk": "chatbot conversation",
    "chat": "chatbot conversation assistant",
    "write": "writing text content",
    "blog": "writing content seo",
    "email": "writing marketing",
    "dev": "code developer programming",
    "build": "code developer",
    "develop": "code developer programming",
    "search": "research web information",
    "find": "research search",
    "learn": "education research",
    "meeting": "transcription notes",
    "note": "productivity notes",
    "design": "visual creative",
    "poster": "design image creative",
    "presentation": "slides design",
}

def expand_query(query: str) -> str:
    """Expand user query with synonym enrichment."""
    words = query.lower().split()
    expanded = list(words)
    for word in words:
        if word in KEYWORD_SYNONYMS:
            expanded.extend(KEYWORD_SYNONYMS[word].split())
    return " ".join(expanded)

# ─── Recommendation Engine ────────────────────────────────────────────────────
def recommend(query: str, top_n: int = 6, filters: dict = None):
    """Core ML recommendation using TF-IDF + cosine similarity."""
    expanded = expand_query(query)
    query_vec = vectorizer.transform([expanded])
    scores = cosine_similarity(query_vec, tfidf_matrix).flatten()

    # Apply filters
    filtered_tools = list(enumerate(tools))
    if filters:
        if filters.get("category") and filters["category"] != "all":
            filtered_tools = [
                (i, t) for i, t in filtered_tools
                if t["category"].lower() == filters["category"].lower()
            ]
        if filters.get("pricing") and filters["pricing"] != "all":
            filtered_tools = [
                (i, t) for i, t in filtered_tools
                if t["pricing"].lower() == filters["pricing"].lower()
            ]
        if filters.get("difficulty") and filters["difficulty"] != "all":
            filtered_tools = [
                (i, t) for i, t in filtered_tools
                if t["difficulty"].lower() == filters["difficulty"].lower()
            ]

    # Rank by similarity score
    ranked = sorted(
        [(i, t, float(scores[i])) for i, t in filtered_tools],
        key=lambda x: x[2], reverse=True
    )

    results = []
    for i, tool, score in ranked[:top_n]:
        results.append({
            **tool,
            "score": round(score * 100, 1),
            "match_percent": min(100, round(score * 200, 0))
        })

    return results

# ─── Routes ───────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    categories = sorted(set(t["category"] for t in tools))
    featured = tools[:6]
    return render_template("index.html", categories=categories, featured=featured)

@app.route("/api/recommend", methods=["POST"])
def api_recommend():
    body = request.get_json()
    if not body:
        return jsonify({"error": "Invalid JSON body"}), 400

    query = body.get("query", "").strip()
    filters = body.get("filters", {})
    top_n = int(body.get("top_n", 6))

    if not query:
        return jsonify({"error": "Query cannot be empty"}), 400

    results = recommend(query, top_n=top_n, filters=filters)
    return jsonify({
        "query": query,
        "expanded_query": expand_query(query),
        "count": len(results),
        "results": results
    })

@app.route("/api/tools", methods=["GET"])
def api_all_tools():
    return jsonify(tools)

@app.route("/api/categories", methods=["GET"])
def api_categories():
    categories = sorted(set(t["category"] for t in tools))
    return jsonify(categories)

# ─── Entry Point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)