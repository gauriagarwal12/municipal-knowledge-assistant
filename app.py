import os
from pathlib import Path
from flask import send_from_directory
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
from agent import MunicipalAgent

load_dotenv()

app = Flask(__name__)
# Serve the original municipal PDFs so source links can open them.
BASE_DIR = Path(__file__).resolve().parent
PDF_DIR = BASE_DIR / "data"


@app.route("/documents/<path:filename>")
def serve_document(filename):
    return send_from_directory(PDF_DIR, filename)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024  # 32 KB JSON request limit

agent = MunicipalAgent()

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/health")
def health():
    return jsonify({"status": "ok", "documents_loaded": agent.retriever.document_count})

@app.post("/chat")
def chat():
    if not request.is_json:
        return jsonify({"error": "Send a JSON request with a 'message' field."}), 400

    payload = request.get_json(silent=True) or {}
    message = payload.get("message")

    if not isinstance(message, str) or not message.strip():
        return jsonify({"error": "Please enter a question."}), 400
    if len(message) > 2000:
        return jsonify({"error": "Please keep your question under 2,000 characters."}), 400

    try:
        result = agent.answer(message.strip())
        return jsonify(result), 200
    except Exception:
        app.logger.exception("Chat request failed")
        return jsonify({
            "answer": "Sorry, the assistant is temporarily unavailable. Please try again.",
            "sources": [],
            "error": "The AI service or retrieval pipeline failed."
        }), 502

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")