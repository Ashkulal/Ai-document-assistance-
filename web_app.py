import os
import json
import tempfile
import requests
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from assistant import DocumentAssistant

load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

assistant = None
resume_content = None
resume_name = None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/upload", methods=["POST"])
def upload():
    global assistant, resume_content, resume_name
    api_key = request.form.get("api_key", "")
    base_url = request.form.get("base_url", "https://openrouter.ai/api/v1")
    model = request.form.get("model", "")
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
        resume_name = filename

    try:
        assistant = DocumentAssistant(api_key=api_key, model_name=model, base_url=base_url)
        num_chunks = assistant.ingest_documents(file_paths)

        from document_loader import load_documents
        docs = load_documents(file_paths)
        resume_content = "\n\n".join(d.page_content for d in docs)[:4000]

        return jsonify({
            "success": True,
            "chunks": num_chunks,
            "files": len(files),
            "resume_preview": resume_content[:500],
            "resume_name": resume_name,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/models", methods=["POST"])
def get_models():
    data = request.json
    base_url = data.get("base_url", "https://openrouter.ai/api/v1")
    api_key = data.get("api_key", "")

    try:
        url = base_url.rstrip("/") + "/models"
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            return jsonify({"error": f"API returned status {res.status_code}"}), 400

        data = res.json()
        models = []
        for m in data.get("data", []):
            model_id = m.get("id", "")
            name = m.get("name", model_id)
            ctx = m.get("context_length", 0)
            ctx_str = f"{ctx // 1024}K" if ctx >= 1024 else str(ctx)
            models.append({"id": model_id, "name": name, "ctx": ctx_str})

        models.sort(key=lambda x: x["name"])
        return jsonify({"models": models})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/mcq", methods=["POST"])
def generate_mcq():
    global assistant, resume_content
    data = request.json
    round_type = data.get("round_type", "aptitude")
    count = data.get("count", 30)

    if not assistant:
        return jsonify({"error": "No documents loaded"}), 400

    resume_section = f"\n\nRESUME:\n{resume_content}" if resume_content else ""

    if round_type == "aptitude":
        prompt = f"""Generate 30 aptitude multiple choice questions for a job interview.
Match the candidate's education from this resume:
{resume_section}

Include: logical reasoning, numerical ability, pattern recognition, data interpretation.

Return ONLY a valid JSON array. Each item has: q, A, B, C, D, answer, explanation.
answer is one letter: A, B, C, or D.

Example:
[{{"q":"What is 15% of 200?","A":"25","B":"30","C":"35","D":"40","answer":"B","explanation":"15x2=30"}}]

Return the JSON array only. No other text."""

    elif round_type == "technical":
        prompt = f"""Generate 30 technical multiple choice questions based on this resume:
{resume_section}

Cover programming, data structures, algorithms, databases, OS, networking, and skills from the resume.

Return ONLY a valid JSON array. Each item has: q, A, B, C, D, answer, explanation.
answer is one letter: A, B, C, or D.

Example:
[{{"q":"Time complexity of binary search?","A":"O(n)","B":"O(log n)","C":"O(n log n)","D":"O(1)","answer":"B","explanation":"Halves search space each step"}}]

Return the JSON array only. No other text."""

    else:
        return jsonify({"error": "Invalid round type"}), 400

    try:
        result = assistant.ask(prompt)
        raw = result["answer"].strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        if raw.startswith("["):
            questions = json.loads(raw)
        else:
            start = raw.find("[")
            end = raw.rfind("]") + 1
            if start >= 0 and end > start:
                questions = json.loads(raw[start:end])
            else:
                return jsonify({"error": "Model did not return valid JSON. Try again."}), 500
        return jsonify({"questions": questions})
    except json.JSONDecodeError:
        return jsonify({"error": "Failed to parse questions. Try again."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/coding", methods=["POST"])
def generate_coding():
    global assistant, resume_content
    data = request.json
    difficulty = data.get("difficulty", "medium")

    if not assistant:
        return jsonify({"error": "No documents loaded"}), 400

    resume_section = f"\n\nRESUME:\n{resume_content}" if resume_content else ""

    prompt = f"""Generate a coding problem for a candidate with these skills:
{resume_section}

Difficulty: {difficulty}

Return ONLY a valid JSON object:
{{"title":"problem title","description":"problem description with input/output format","examples":[{{"input":"ex input","output":"ex output","explanation":"how"}}],"constraints":"constraints","test_cases":[{{"input":"test1","output":"result1"}},{{"input":"test2","output":"result2"}}],"starter_code":"function signature","language":"python"}}

Return JSON only. No markdown, no other text."""

    try:
        result = assistant.ask(prompt)
        raw = result["answer"].strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        if raw.startswith("{"):
            problem = json.loads(raw)
        else:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start >= 0 and end > start:
                problem = json.loads(raw[start:end])
            else:
                return jsonify({"error": "Model did not return valid JSON. Try again."}), 500
        return jsonify({"problem": problem})
    except json.JSONDecodeError:
        return jsonify({"error": "Failed to parse problem. Try again."}), 500
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


if __name__ == "__main__":
    app.run(debug=True, port=5000)
