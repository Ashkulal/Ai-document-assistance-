import os
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


resume_content = None


@app.route("/api/upload", methods=["POST"])
def upload():
    global assistant, resume_content
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

        # Extract raw resume text for interview
        from document_loader import load_documents
        docs = load_documents(file_paths)
        resume_content = "\n\n".join(d.page_content for d in docs)[:3000]

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
    global assistant, resume_content
    data = request.json
    round_type = data.get("round_type", "all")
    difficulty = data.get("difficulty", "all")

    if not assistant:
        return jsonify({"error": "No documents loaded"}), 400

    resume_section = f"\n\nRESUME CONTENT:\n{resume_content}" if resume_content else ""

    prompts = {
        "aptitude": f"""You are a professional interview coach. The candidate uploaded this resume:{resume_section}

FIRST: Identify the candidate's field (CS, ECE, MBA, etc.) and role target (developer, analyst, manager, etc.)

THEN generate 10 aptitude questions TAILORED to their field:
- For CS/Engineering candidates: include logical reasoning, pattern recognition, basic math, coding logic
- For MBA/Business candidates: include data interpretation, business reasoning, quantitative aptitude, logical reasoning
- For general candidates: mix of verbal, non-verbal, and quantitative

Each question must be realistic and relevant to their target role.
Format each as: number. question (answer in parentheses)

Example for a CS student:
1. If an array of n elements is sorted, what is the minimum number of comparisons needed to find an element? (log n)
2. A function f(n) = 2*f(n-1) + 1, f(0) = 0. What is f(4)? (31)""",

        "technical": f"""You are a senior technical interviewer. The candidate uploaded this resume:{resume_section}

FIRST: Extract from the resume:
1. Programming languages they know
2. Frameworks/tools they use
3. Projects they built (with tech stack)
4. Areas of expertise (web, mobile, AI, cloud, etc.)
5. Internship/work experience technologies

THEN generate 10 technical questions SPECIFICALLY based on what you found:
- Ask about technologies THEY listed (not generic)
- Ask about THEIR projects in detail
- Ask design questions relevant to THEIR stack
- Include [Easy], [Medium], [Hard] tags
- Ask "how would you improve X project?" type questions

Format: number. [Easy/Medium/Hard] question""",

        "hr": f"""You are an experienced HR interviewer. The candidate uploaded this resume:{resume_section}

FIRST: Identify from the resume:
1. Their education background
2. Career gaps or transitions
3. Internship/company names
4. Achievements and awards
5. Career goal hints

THEN generate 10 HR questions SPECIFICALLY relevant to their profile:
- Ask about THEIR specific experiences
- Address potential concerns from THEIR resume
- Ask about THEIR career goals
- Include behavioral + situational questions
- Make it feel like a real HR screening

Format: number. question""",

        "behavioral": f"""You are a behavioral interview specialist. The candidate uploaded this resume:{resume_section}

FIRST: Identify from the resume:
1. Team projects they worked on
2. Leadership roles held
3. Challenges mentioned in projects
4. Achievements and competitions
5. Volunteer work or extracurriculars

THEN generate 10 behavioral questions using STAR method, SPECIFICALLY about:
- Challenges in THEIR projects
- Leadership in THEIR roles
- Team conflicts THEY might have faced
- Failures and learnings from THEIR experience
- Time management with THEIR activities

Format: number. question""",
    }

    prompt = prompts.get(round_type, prompts["technical"])

    try:
        result = assistant.ask(prompt)
        return jsonify({"answer": result["answer"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/evaluate", methods=["POST"])
def evaluate():
    global assistant
    data = request.json
    question = data.get("question", "")
    answer = data.get("answer", "")
    round_type = data.get("round_type", "technical")

    if not assistant:
        return jsonify({"error": "No documents loaded"}), 400

    resume_section = f"\n\nRESUME CONTEXT:\n{resume_content}" if resume_content else ""

    prompt = f"""You are a strict but fair interview evaluator. The candidate is being interviewed for a role relevant to their resume.
{resume_section}

Question asked: {question}
Candidate's answer: {answer}

Evaluate their answer:
1. Is it technically correct?
2. Is it complete and detailed?
3. Does it show real understanding or just surface knowledge?
4. Could they have added anything from their own experience?

Respond in this EXACT format:
SCORE: [1-10]
FEEDBACK: [1-2 sentence honest feedback]
KEY_POINTS: [2-3 things they missed or could improve]"""

    try:
        result = assistant.ask(prompt)
        return jsonify({"evaluation": result["answer"]})
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


if __name__ == "__main__":
    app.run(debug=True, port=5000)
