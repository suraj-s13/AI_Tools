import uuid
from flask import Flask, render_template, request, jsonify, session

import model as recommender
import feedback as fb_module

app = Flask(__name__)
app.secret_key = 'your-secret-key'

@app.route('/')
def index():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.get_json(force=True, silent=True) or {}
    query = (data.get("query") or "").strip()

    if not query:
        return jsonify({"error": "Query cannot be empty."}), 400

    if len(query) > 500:
        return jsonify({"error": "Query is too long. Maximum length is 500 characters."}), 400

    try:
        results = recommender.get_recommendations(query, top_n=5)
        session["last_query"] = query
        return jsonify({"query": query, "recommendations": results})
    except Exception as exc:
        retrun jsonify({"error": f"Recommendation failed: {str(exc)}"}), 500

@app.route('/feedback', methods=['POST'])
def feedback():
    data = request.get_json(force=True, silent=True) or {}
    query = (data.get("query") or session.get("last_query", "")).strip()
    tool_name = (data.get("tool_name") or "").strip()
    vote = (data.get("feedback") or "").strip()
    sid = session.get("session_id", str(uuid.uuid4()))

    if not tool_name or vote not in ("useful", "not_useful"):
        return jsonify({"error": "Invalid feedback payload."}), 400

    success = fb_module.save_feedback(query, tool_name, vote, sid)
    if success:
        return jsonify({"status": "ok", "message": f"Feedback recorded for {tool_name}."})
    return jsonify({"error": "Failed to save feedback."}), 500

@app.route("/update-model", methods=["POST"])
def update_model():
    try:
        recommender.train_model()
        stats = fb_module.get_feedback_stats()
        return jsonify({
            "status": "ok",
            "message": "Model retrained successfully.",
            "feedback_stats": stats,
        })
    except Exception as exc:
        return jsonify({"error": f"Retraining failed: {str(exc)}"}), 500


@app.route("/stats")
def stats():
    return jsonify(fb_module.get_feedback_stats())


if __name__ == "__main__":
    # Pre-warm the model on startup
    print("Loading and training recommendation model...")
    recommender.train_model()
    print("Model ready. Starting Flask server...")
    app.run(debug=True, port=5000)
