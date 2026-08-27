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

    resume_section = f"\n\nRESUME:\n{resume_content}" if resume_content else ""

    prompts = {
        "aptitude": f"""You are a sharp interviewer. Read the candidate's resume below.
{resume_section}

Based on their EDUCATION and FIELD, generate 10 aptitude questions:
- Match their degree level (B.Tech/MBA/etc)
- Include logical reasoning, numerical, pattern-based questions
- 3 Easy, 4 Medium, 3 Hard

Format: number. question
Answer each question yourself in (parentheses) after the question.""",

        "technical": f"""You are a ruthless technical interviewer. Read the candidate's resume below.
{resume_section}

Look at EVERY skill, project, and technology listed. Now grill them:

1. Ask about each major skill/project listed — deep not surface level
2. "You mention X in your resume — how does it work under the hood?"
3. "Your project uses Y — why did you choose Y over alternatives?"
4. "If Z breaks in production, how do you debug it?"
5. Mix coding problems related to their tech stack
6. Ask system design based on their project scale
7. 3 Easy, 4 Medium, 3 Hard

Generate 10 questions. Format: number. question""",

        "hr": f"""You are a sharp HR interviewer. Read the candidate's resume below.
{resume_section}

Look at their CAREER PATH, education gaps, job switches, achievements. Now ask:

1. Questions that probe their actual experiences listed
2. "I see you worked at [company] — tell me about your biggest challenge there"
3. "You studied [degree] — why that field?"
4. Questions about gaps, transitions, choices visible in the resume
5. Strengths/weaknesses related to THEIR profile
6. Where they see themselves going based on THEIR trajectory

Generate 10 questions. Format: number. question""",

        "behavioral": f"""You are a behavioral interview expert. Read the candidate's resume below.
{resume_section}

Look at their PROJECTS, TEAM WORK, LEADERSHIP, EXTRACURRICULARS. Now ask STAR questions about THEIR actual experiences:

1. "Tell me about a time during [their specific project] when things went wrong"
2. "Describe your role in [their team project]"
3. "Give an example of how you handled [challenge relevant to their field]"
4. "Tell me about a disagreement with a teammate during [their project]"
5. Questions drawn from THEIR activities and experiences

Generate 10 questions. Format: number. question""",
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
