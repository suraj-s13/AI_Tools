import os
import uuid
import csv
from datetime import datetime

FEEDBACK_PATH = os.path.join(os.path.dirname(__file__), "feedback", "feedback.csv")
FIELDNAMES = ["timestamp", "query", "tool_name", "feedback", "session_id"]


def _ensure_feedback_file():
    os.makedirs(os.path.dirname(FEEDBACK_PATH), exist_ok=True)
    if not os.path.exists(FEEDBACK_PATH):
        with open(FEEDBACK_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()


def save_feedback(query: str, tool_name: str, feedback: str, session_id: str = None) -> bool:
    _ensure_feedback_file()

    if feedback not in ("useful", "not_useful"):
        return False

    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "query": query.strip(),
        "tool_name": tool_name.strip(),
        "feedback": feedback,
        "session_id": session_id or str(uuid.uuid4()),
    }

    try:
        with open(FEEDBACK_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writerow(record)
        return True
    except Exception:
        return False


def get_feedback_stats() -> dict:
    _ensure_feedback_file()
    stats = {"total": 0, "useful": 0, "not_useful": 0, "by_tool": {}}

    try:
        import pandas as pd

        df = pd.read_csv(FEEDBACK_PATH)
        if df.empty:
            return stats

        stats["total"] = len(df)
        stats["useful"] = int((df["feedback"] == "useful").sum())
        stats["not_useful"] = int((df["feedback"] == "not_useful").sum())

        for tool, group in df.groupby("tool_name"):
            stats["by_tool"][tool] = {
                "useful": int((group["feedback"] == "useful").sum()),
                "not_useful": int((group["feedback"] == "not_useful").sum()),
            }
    except Exception:
        pass

    return stats
