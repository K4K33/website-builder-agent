from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="")


@app.get("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "agent": "Website Builder Agent",
        "mode": "local"
    })


@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()

    if not message:
        return jsonify({
            "error": "Message cannot be empty."
        }), 400

    # First UI version intentionally uses a local response.
    # Real agent commands will be connected after the UI is verified.
    response = (
        "I received your message. "
        "The agent interface is working, but real agent commands "
        "have not been connected yet."
    )

    return jsonify({
        "message": response,
        "mode": "local"
    })


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=8000,
        debug=False
    )
