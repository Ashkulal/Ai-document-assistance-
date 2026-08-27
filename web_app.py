import os
import tempfile
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from assistant import DocumentAssistant

load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

assistant = None

MODELS = [
    {"id": "nvidia/nemotron-3-ultra-550b-a55b:free", "name": "Nemotron 3 Ultra", "provider": "NVIDIA", "ctx": "1M"},
    {"id": "nvidia/nemotron-3.5-lightning:free", "name": "Nemotron 3.5 Lightning", "provider": "NVIDIA", "ctx": "1M"},
    {"id": "nvidia/nemotron-3-super-120b-a12b:free", "name": "Nemotron 3 Super", "provider": "NVIDIA", "ctx": "262K"},
    {"id": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free", "name": "Nemotron 3 Nano Omni", "provider": "NVIDIA", "ctx": "256K"},
    {"id": "nvidia/nemotron-3-nano-30b-a3b:free", "name": "Nemotron 3 Nano", "provider": "NVIDIA", "ctx": "256K"},
    {"id": "nvidia/nemotron-nano-9b-v2:free", "name": "Nemotron Nano 9B", "provider": "NVIDIA", "ctx": "128K"},
    {"id": "minimax/minimax-m3:free", "name": "MiniMax M3", "provider": "MiniMax", "ctx": "1M"},
    {"id": "minimax/minimax-m2.7:free", "name": "MiniMax M2.7", "provider": "MiniMax", "ctx": "197K"},
    {"id": "cohere/north-mini-code:free", "name": "North Mini Code", "provider": "Cohere", "ctx": "256K"},
    {"id": "poolside/laguna-s-2.1:free", "name": "Laguna S 2.1", "provider": "Poolside", "ctx": "262K"},
    {"id": "poolside/laguna-xs-2.1:free", "name": "Laguna XS 2.1", "provider": "Poolside", "ctx": "262K"},
    {"id": "dots-studio/dots-3-note-preview:free", "name": "Dots3-Note", "provider": "Dots Studio", "ctx": "512K"},
    {"id": "thinkingmachines/inkling:free", "name": "Inkling", "provider": "Thinking Machines", "ctx": "262K"},
    {"id": "thinkingmachines/inkling-small:free", "name": "Inkling Small", "provider": "Thinking Machines", "ctx": "262K"},
    {"id": "z-ai/glm-5.2:free", "name": "GLM 5.2", "provider": "Z.ai", "ctx": "256K"},
    {"id": "liquid/lfm-2.5-2.6b:free", "name": "LFM 2.5 2.6B", "provider": "LiquidAI", "ctx": "66K"},
    {"id": "google/gemma-4-31b-it:free", "name": "Gemma 4 31B", "provider": "Google", "ctx": "262K"},
    {"id": "google/gemma-4-26b-a4b-it:free", "name": "Gemma 4 26B", "provider": "Google", "ctx": "262K"},
    {"id": "openai/gpt-oss-20b:free", "name": "GPT-OSS 20B", "provider": "OpenAI", "ctx": "131K"},
]


@app.route("/")
def index():
    return render_template("index.html", models=MODELS)


@app.route("/api/upload", methods=["POST"])
def upload():
    global assistant
    api_key = request.form.get("api_key", "")
    base_url = request.form.get("base_url", "https://openrouter.ai/api/v1")
    model = request.form.get("model", MODELS[0]["id"])
    files = request.files.getlist("files")

    if not api_key:
        return jsonify({"error": "API key required"}), 400
    if not files:
        return jsonify({"error": "No files uploaded"}), 400

    temp_dir = tempfile.mkdtemp()
    file_paths = []
    for f in files:
        filename = secure_filename(f.filename)
        path = os.path.join(temp_dir, filename)
        f.save(path)
        file_paths.append(path)

    try:
        assistant = DocumentAssistant(api_key=api_key, model_name=model, base_url=base_url)
        num_chunks = assistant.ingest_documents(file_paths)
        return jsonify({"success": True, "chunks": num_chunks, "files": len(files)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ask", methods=["POST"])
def ask():
    global assistant
    data = request.json
    question = data.get("question", "")

    if not assistant:
        return jsonify({"error": "No documents loaded"}), 400
    if not question:
        return jsonify({"error": "No question provided"}), 400

    try:
        result = assistant.ask(question)
        return jsonify({
            "answer": result["answer"],
            "sources": [s.get("source", "unknown") for s in result.get("sources", [])],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/interview", methods=["POST"])
def interview():
    global assistant
    data = request.json
    difficulty = data.get("difficulty", "all")

    if not assistant:
        return jsonify({"error": "No documents loaded"}), 400

    prompt = f"""Based on the uploaded resume, generate interview questions at {difficulty} difficulty level.

Format your response EXACTLY like this (no extra text):

## Easy (Low)
1. [question]
2. [question]
3. [question]
4. [question]
5. [question]

## Medium (Mid)
1. [question]
2. [question]
3. [question]
4. [question]
5. [question]

## Tough (High)
1. [question]
2. [question]
3. [question]
4. [question]
5. [question]

Generate 5 questions for EACH level. Base questions on the candidate's skills, projects, internship, and education from the resume."""

    if difficulty == "easy":
        prompt = "Based on the uploaded resume, generate 10 easy/low-level interview questions. These should be basic questions about the candidate's background, education, and simple skill checks. Format: numbered list."
    elif difficulty == "medium":
        prompt = "Based on the uploaded resume, generate 10 medium-level interview questions. These should test project experience, technical depth, and problem-solving. Format: numbered list."
    elif difficulty == "tough":
        prompt = "Based on the uploaded resume, generate 10 tough/hard-level interview questions. These should be challenging system design, architecture, and deep technical questions based on their tech stack. Format: numbered list."

    try:
        result = assistant.ask(prompt)
        return jsonify({"answer": result["answer"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
