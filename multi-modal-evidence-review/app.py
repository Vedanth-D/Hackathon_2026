"""
Web dashboard for the Multi-Modal Evidence Review system.

Wraps the existing src/claim_reviewer.ClaimReviewer pipeline with a
small Flask UI: upload claim photos + description -> get a verdict.

Run:
    pip install -r requirements-web.txt
    python app.py
Then open http://127.0.0.1:5000 in your browser.
"""

import logging
import uuid
from pathlib import Path

from flask import Flask, render_template, request, jsonify

from src.claim_reviewer import ClaimReviewer
from src.config import DATASET_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25 MB total upload cap

# Reviewer instance is created lazily per-request mode (mock vs live)
# so the dashboard works even without an OPENAI_API_KEY set.
_reviewers = {}


def get_reviewer(mock_mode: bool) -> ClaimReviewer:
    if mock_mode not in _reviewers:
        _reviewers[mock_mode] = ClaimReviewer(str(DATASET_DIR), mock_mode=mock_mode)
    return _reviewers[mock_mode]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/review", methods=["POST"])
def review():
    user_id = request.form.get("user_id", "web_user")
    user_claim = request.form.get("user_claim", "").strip()
    claim_object = request.form.get("claim_object", "car")
    mock_mode = request.form.get("mock_mode", "true").lower() == "true"

    if not user_claim:
        return jsonify({"error": "Please describe the damage/claim."}), 400

    files = request.files.getlist("images")
    if not files or all(f.filename == "" for f in files):
        return jsonify({"error": "Please upload at least one image."}), 400

    # Save uploads to a unique session subfolder
    session_id = uuid.uuid4().hex[:10]
    session_dir = UPLOAD_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    saved_paths = []
    for f in files:
        if not f.filename:
            continue
        ext = Path(f.filename).suffix.lower()
        if ext not in ALLOWED_EXT:
            continue
        dest = session_dir / f.filename
        f.save(dest)
        saved_paths.append(str(dest.resolve()))

    if not saved_paths:
        return jsonify({"error": "No valid image files (jpg/jpeg/png/webp)."}), 400

    row = {
        "user_id": user_id,
        "image_paths": ";".join(saved_paths),
        "user_claim": user_claim,
        "claim_object": claim_object,
    }

    try:
        reviewer = get_reviewer(mock_mode)
        result = reviewer.review_claim(row)
        return jsonify(result.to_row())
    except Exception as e:
        logger.exception("Review failed")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
