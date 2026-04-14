# AI Tools Recommendation System

An ML-powered web application that recommends relevant AI tools based on natural language problem descriptions. Uses TF-IDF similarity with feedback-based weight learning.

---

## Project Structure

```
project/
├── app.py              ← Flask routes & session management
├── model.py            ← TF-IDF ML engine (train + recommend)
├── feedback.py         ← Feedback storage & statistics
├── requirements.txt    ← Python dependencies
│
├── dataset/
│   └── ai_tools.csv    ← 40+ AI tools with descriptions & keywords
│
├── feedback/
│   └── feedback.csv    ← Persisted user votes (auto-created)
│
├── templates/
│   └── index.html      ← Main HTML template (Jinja2)
│
└── static/
    └── css/
        ├── style.css   ← Full UI stylesheet
        └── main.js     ← Frontend logic (fetch, render, feedback)
```

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the application
```bash
python app.py
```

### 3. Open in browser
```
http://localhost:5000
```

---

## Features

| Feature | Details |
|---------|---------|
| **NLP Matching** | TF-IDF vectorization with bigrams on tool name + category + description + keywords |
| **Similarity** | Cosine similarity between user query and all tool vectors |
| **Feedback Learning** | 👍 = +15% weight boost · 👎 = −10% weight penalty |
| **Model Update** | Click "Update Model" button or POST `/update-model` to retrain |
| **Dataset** | 40+ tools across 15+ categories (easily extendable) |
| **Search Hints** | Pre-built example queries for quick testing |

---

## API Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Homepage |
| `/recommend` | POST | Get tool recommendations for a query |
| `/feedback` | POST | Submit 👍 / 👎 for a recommendation |
| `/update-model` | POST | Retrain model with latest feedback |
| `/stats` | GET | View feedback statistics (JSON) |

### `/recommend` Request
```json
{ "query": "I want to create AI videos" }
```

### `/recommend` Response
```json
{
  "query": "I want to create AI videos",
  "recommendations": [
    {
      "tool_name": "Runway ML",
      "category": "Video Generation",
      "description": "...",
      "icon_url": "https://...",
      "website_link": "https://runwayml.com",
      "score": 0.432,
      "rank": 1
    }
  ]
}
```

### `/feedback` Request
```json
{
  "query": "I want to create AI videos",
  "tool_name": "Runway ML",
  "feedback": "useful"
}
```

---

## Expanding the Dataset

Add rows to `dataset/ai_tools.csv` with these columns:
```
tool_name, category, description, keywords, icon_url, website_link
```

Then click **Update Model** in the UI or POST to `/update-model` to reload.

---

## How the ML Works

1. **Preprocessing** — Lowercase + strip punctuation from all text fields
2. **TF-IDF** — Builds a term-frequency matrix with bigrams across the corpus
3. **Query Vectorization** — Transforms user input using the same vocabulary
4. **Cosine Similarity** — Measures angle between query vector and each tool vector
5. **Feedback Weighting** — Multiplies similarity scores by per-tool weight factors
6. **Ranking** — Returns top-N tools by weighted score
