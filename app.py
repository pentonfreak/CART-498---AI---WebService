"""Flask server for the Museum of Misplaced Meaning.

API credentials stay server-side. The web browser receives the completed exhibit,
not the API key or the original prompt to the image-generation service.
"""

import os
import threading
import time
from collections import defaultdict, deque

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from openai import APIConnectionError, APIError, APITimeoutError, OpenAI, RateLimitError

from museum import generate_exhibition_image, generate_wall_label

load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8192

# Light best-effort protection for a classroom demo; a Redis-backed limiter is
# recommended for a busy public gallery. Tests bypass the limiter.
_hits = defaultdict(deque)
_hits_lock = threading.Lock()


def is_rate_limited(visitor: str) -> bool:
    quota = max(1, int(os.environ.get("MAX_GENERATIONS_PER_HOUR", "8")))
    now = time.monotonic()
    with _hits_lock:
        recent = _hits[visitor]
        while recent and now - recent[0] > 3600:
            recent.popleft()
        if len(recent) >= quota:
            return True
        recent.append(now)
        return False


@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; "
        "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'"
    )
    if request.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/api/generate")
def generate():
    if not request.is_json:
        return jsonify({"error": "Send a JSON object containing 'object_description'."}), 415

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON request."}), 400

    description = data.get("object_description", "")
    if not isinstance(description, str) or not 6 <= len(description.strip()) <= 400:
        return jsonify({"error": "Describe one object in 6–400 characters."}), 400
    description = description.strip()

    secret = os.environ.get("OPENAI_API_KEY", "").strip()
    if not secret:
        return jsonify({"error": "The curator is not configured yet. Add OPENAI_API_KEY on the server."}), 503

    visitor = request.remote_addr or "unknown"
    if not app.config.get("TESTING") and is_rate_limited(visitor):
        return jsonify({"error": "This visitor has reached the hourly exhibition limit. Try again later."}), 429

    try:
        client = OpenAI(api_key=secret, timeout=120.0, max_retries=1)
        label = generate_wall_label(client, description, os.environ.get("TEXT_MODEL", "gpt-5.4-mini"))
        image_url = generate_exhibition_image(client, label, os.environ.get("IMAGE_MODEL", "gpt-image-2.5-flare"))
        return jsonify({"label": label.model_dump(), "image": image_url})
    except RateLimitError:
        return jsonify({"error": "The API is busy or its quota has been reached. Please try later."}), 429
    except (APITimeoutError, APIConnectionError):
        app.logger.warning("OpenAI temporarily unavailable")
        return jsonify({"error": "The image workshop could not be reached. Please retry."}), 502
    except (APIError, ValueError) as exc:
        # Never send provider error strings (which may include request data) to visitors.
        app.logger.warning("Curation failed (%s)", type(exc).__name__)
        return jsonify({"error": "Curation failed. Please try another object or retry."}), 502


@app.errorhandler(413)
def too_large(_error):
    return jsonify({"error": "The description is too long."}), 413


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1", host="127.0.0.1", port=int(os.environ.get("PORT", "5000")))
