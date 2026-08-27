let selectedFiles = [];
let currentMode = "chat";
let currentRound = null;
let questions = [];
let currentQuestionIndex = 0;
let totalScore = 0;
let totalAnswered = 0;
let isRecording = false;
let recognition = null;

const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("fileInput");
const fileList = document.getElementById("fileList");
const processBtn = document.getElementById("processBtn");
const uploadStatus = document.getElementById("uploadStatus");
const statusBadge = document.getElementById("statusBadge");
const chatMessages = document.getElementById("chatMessages");
const questionInput = document.getElementById("questionInput");
const sendBtn = document.getElementById("sendBtn");
const scoreDisplay = document.getElementById("scoreDisplay");
const scoreValue = document.getElementById("scoreValue");

// Auto-fetch models on API key enter
document.getElementById("apiKey").addEventListener("keydown", (e) => {
    if (e.key === "Enter") fetchModels();
});

async function fetchModels() {
    const baseUrl = document.getElementById("baseUrl").value;
    const apiKey = document.getElementById("apiKey").value;
    const modelSelect = document.getElementById("modelSelect");
    const modelStatus = document.getElementById("modelStatus");
    const fetchBtn = document.getElementById("fetchBtn");

    if (!apiKey) {
        modelStatus.className = "status error";
        modelStatus.textContent = "Enter API key first";
        return;
    }

    fetchBtn.disabled = true;
    fetchBtn.textContent = "Loading...";
    modelStatus.className = "status";
    modelStatus.textContent = "Fetching models...";
    modelSelect.innerHTML = '<option value="">Loading...</option>';

    try {
        const res = await fetch("/api/models", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ base_url: baseUrl, api_key: apiKey }),
        });
        const data = await res.json();

        if (data.error) {
            modelSelect.innerHTML = '<option value="">Failed to load</option>';
            modelStatus.className = "status error";
            modelStatus.textContent = data.error;
            return;
        }

        modelSelect.innerHTML = "";
        data.models.forEach((m) => {
            const opt = document.createElement("option");
            opt.value = m.id;
            opt.textContent = `${m.name} (${m.ctx})`;
            modelSelect.appendChild(opt);
        });

        modelStatus.className = "status success";
        modelStatus.textContent = `${data.models.length} models loaded`;
    } catch (err) {
        modelSelect.innerHTML = '<option value="">Failed to load</option>';
        modelStatus.className = "status error";
        modelStatus.textContent = err.message;
    }

    fetchBtn.disabled = false;
    fetchBtn.textContent = "Fetch";
}

// Voice Recognition Setup
if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onresult = (event) => {
        let transcript = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
            transcript += event.results[i][0].transcript;
        }
        questionInput.value = transcript;
        autoResize();
    };

    recognition.onend = () => {
        isRecording = false;
        document.getElementById("voiceBtn").classList.remove("recording");
    };

    recognition.onerror = (event) => {
        isRecording = false;
        document.getElementById("voiceBtn").classList.remove("recording");
        console.error("Speech recognition error:", event.error);
    };
}

// Dropzone
dropzone.addEventListener("click", () => fileInput.click());
dropzone.addEventListener("dragover", (e) => { e.preventDefault(); dropzone.classList.add("dragover"); });
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    addFiles(e.dataTransfer.files);
});
fileInput.addEventListener("change", (e) => addFiles(e.target.files));

function addFiles(files) {
    for (const f of files) {
        if (!selectedFiles.find((s) => s.name === f.name)) {
            selectedFiles.push(f);
        }
    }
    renderFiles();
}

function removeFile(name) {
    selectedFiles = selectedFiles.filter((f) => f.name !== name);
    renderFiles();
}

function renderFiles() {
    fileList.innerHTML = selectedFiles.map((f) =>
        `<div class="file-item"><span class="name">${f.name}</span><button class="remove" onclick="removeFile('${f.name}')">×</button></div>`
    ).join("");
    processBtn.disabled = selectedFiles.length === 0;
}

// Upload
async function uploadFiles() {
    const apiKey = document.getElementById("apiKey").value;
    const baseUrl = document.getElementById("baseUrl").value;
    const model = document.getElementById("modelSelect").value;

    if (!apiKey) {
        uploadStatus.className = "status error";
        uploadStatus.textContent = "Enter API key first";
        return;
    }

    processBtn.disabled = true;
    uploadStatus.className = "status";
    uploadStatus.textContent = "Uploading...";

    const formData = new FormData();
    formData.append("api_key", apiKey);
    formData.append("base_url", baseUrl);
    formData.append("model", model);
    selectedFiles.forEach((f) => formData.append("files", f));

    try {
        const res = await fetch("/api/upload", { method: "POST", body: formData });
        const data = await res.json();

        if (data.success) {
            uploadStatus.className = "status success";
            uploadStatus.textContent = `✅ Indexed ${data.chunks} chunks from ${data.files} file(s)`;
            statusBadge.className = "status-badge ready";
            statusBadge.textContent = "● Ready";
            sendBtn.disabled = false;
            questionInput.focus();
        } else {
            uploadStatus.className = "status error";
            uploadStatus.textContent = `❌ ${data.error}`;
        }
    } catch (err) {
        uploadStatus.className = "status error";
        uploadStatus.textContent = `❌ ${err.message}`;
    }

    processBtn.disabled = false;
}

// Voice Toggle
function toggleVoice() {
    if (!recognition) {
        alert("Voice recognition not supported in this browser. Use Chrome.");
        return;
    }

    if (isRecording) {
        recognition.stop();
        isRecording = false;
        document.getElementById("voiceBtn").classList.remove("recording");
    } else {
        recognition.start();
        isRecording = true;
        document.getElementById("voiceBtn").classList.add("recording");
    }
}

// Mode Toggle
function setMode(mode) {
    currentMode = mode;
    document.getElementById("chatMode").classList.toggle("active", mode === "chat");
    document.getElementById("interviewMode").classList.toggle("active", mode === "interview");
    document.getElementById("interviewPanel").style.display = mode === "interview" ? "block" : "none";
}

// Start Round
async function startRound(roundType) {
    const statusBadge = document.getElementById("statusBadge");
    if (statusBadge.textContent.includes("No documents")) {
        alert("Upload a resume first!");
        return;
    }

    currentRound = roundType;
    document.getElementById("difficultySelector").style.display = "block";
    document.getElementById("activeRound").style.display = "none";

    const roundNames = {
        aptitude: "📝 Aptitude Round",
        technical: "💻 Technical Round",
        hr: "🤝 HR Round",
        behavioral: "🧠 Behavioral Round"
    };

    addMessage("system", `Starting ${roundNames[roundType]} - Choose difficulty`);
}

// Generate Questions
async function generateQuestions(difficulty) {
    document.getElementById("difficultySelector").style.display = "none";

    const welcome = chatMessages.querySelector(".welcome-message");
    if (welcome) welcome.remove();

    addMessage("system", `Starting ${currentRound.charAt(0).toUpperCase() + currentRound.slice(1)} Round — ${difficulty} level`);

    const typing = addTyping();

    try {
        const res = await fetch("/api/interview", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ round_type: currentRound, difficulty }),
        });
        const data = await res.json();

        typing.remove();

        if (data.error) {
            addMessage("error", data.error);
            return;
        }

        // Parse questions
        questions = parseQuestions(data.answer);
        currentQuestionIndex = 0;
        totalScore = 0;
        totalAnswered = 0;

        if (questions.length === 0) {
            addMessage("error", "No questions generated. Try again.");
            return;
        }

        // Show round info
        showActiveRound();

        // Show intro message with question count
        const introMsg = document.createElement("div");
        introMsg.className = "message assistant";
        introMsg.innerHTML = `<strong>${questions.length} questions</strong> generated based on your resume. Let's begin!<br><br>Answer each question and press Enter or click Send.`;
        chatMessages.appendChild(introMsg);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Show first question after delay
        setTimeout(() => showQuestion(0), 1000);

    } catch (err) {
        typing.remove();
        addMessage("error", err.message);
    }
}

function parseQuestions(text) {
    const lines = text.split("\n");
    const qs = [];
    for (const line of lines) {
        const match = line.match(/^\d+[\.\)]\s*(.+)/);
        if (match) {
            qs.push(match[1].trim());
        }
    }
    return qs;
}

function showActiveRound() {
    const roundNames = {
        aptitude: "📝 Aptitude",
        technical: "💻 Technical",
        hr: "🤝 HR",
        behavioral: "🧠 Behavioral"
    };

    document.getElementById("activeRound").style.display = "flex";
    document.getElementById("roundBadge").textContent = roundNames[currentRound];
    document.getElementById("questionCounter").textContent = `Q${currentQuestionIndex + 1}/${questions.length}`;
    scoreDisplay.style.display = "block";
}

function showQuestion(index) {
    if (index >= questions.length) {
        finishRound();
        return;
    }

    const msg = document.createElement("div");
    msg.className = "message question-msg";
    msg.innerHTML = `<strong>Question ${index + 1}:</strong> ${questions[index]}`;
    chatMessages.appendChild(msg);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    document.getElementById("questionCounter").textContent = `Q${currentQuestionIndex + 1}/${questions.length}`;
}

// Send Answer
async function sendAnswer() {
    const answer = questionInput.value.trim();
    if (!answer || !questions.length) return;

    questionInput.value = "";
    questionInput.style.height = "auto";

    addMessage("user", answer);

    const typing = addTyping();

    try {
        const res = await fetch("/api/evaluate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                question: questions[currentQuestionIndex],
                answer: answer,
                round_type: currentRound
            }),
        });
        const data = await res.json();

        typing.remove();

        if (data.error) {
            addMessage("error", data.error);
            return;
        }

        // Parse score
        const scoreMatch = data.evaluation.match(/SCORE:\s*(\d+)/i);
        const score = scoreMatch ? parseInt(scoreMatch[1]) : 0;

        totalScore += score;
        totalAnswered++;

        // Show evaluation
        const evalMsg = document.createElement("div");
        evalMsg.className = "message evaluation";
        evalMsg.innerHTML = formatEvaluation(data.evaluation, score);
        chatMessages.appendChild(evalMsg);

        // Update score
        const avgScore = (totalScore / totalAnswered).toFixed(1);
        scoreValue.textContent = `${avgScore}/10`;
        scoreValue.style.color = avgScore >= 7 ? "#22c55e" : avgScore >= 5 ? "#f59e0b" : "#ef4444";

        // Next question
        currentQuestionIndex++;
        chatMessages.scrollTop = chatMessages.scrollHeight;

        setTimeout(() => {
            showQuestion(currentQuestionIndex);
        }, 1500);

    } catch (err) {
        typing.remove();
        addMessage("error", err.message);
    }
}

function formatEvaluation(text, score) {
    let formatted = text;
    formatted = formatted.replace(/SCORE:\s*\d+/i, "");
    formatted = formatted.replace(/KEY_POINTS:/i, "<br><strong>Key Points:</strong>");
    formatted = formatted.replace(/FEEDBACK:/i, "<strong>Feedback:</strong>");
    formatted = formatted.replace(/\n/g, "<br>");

    const scoreColor = score >= 7 ? "#22c55e" : score >= 5 ? "#f59e0b" : "#ef4444";
    return `<div style="margin-bottom:0.5rem;"><span style="font-size:1.5rem;font-weight:700;color:${scoreColor};">${score}/10</span></div>${formatted}`;
}

function finishRound() {
    const avgScore = totalAnswered > 0 ? (totalScore / totalAnswered).toFixed(1) : 0;
    const grade = avgScore >= 9 ? "A+" : avgScore >= 8 ? "A" : avgScore >= 7 ? "B+" : avgScore >= 6 ? "B" : avgScore >= 5 ? "C" : "D";

    const summary = document.createElement("div");
    summary.className = "message assistant";
    summary.innerHTML = `
        <div style="text-align:center;">
            <h3 style="margin-bottom:1rem;">🎉 Round Complete!</h3>
            <div style="font-size:2rem;font-weight:700;color:${avgScore >= 7 ? '#22c55e' : '#f59e0b'};">${avgScore}/10</div>
            <div style="font-size:1.2rem;margin:0.5rem 0;">Grade: ${grade}</div>
            <div style="color:var(--text-secondary);">Questions Answered: ${totalAnswered}</div>
        </div>
    `;
    chatMessages.appendChild(summary);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    endRound();
}

function endRound() {
    currentRound = null;
    questions = [];
    currentQuestionIndex = 0;
    document.getElementById("activeRound").style.display = "none";
    document.getElementById("difficultySelector").style.display = "block";
}

// Helpers
function addMessage(type, text) {
    const msg = document.createElement("div");
    msg.className = `message ${type}`;
    if (type === "system") {
        msg.innerHTML = `<em>${text}</em>`;
        msg.style.textAlign = "center";
        msg.style.color = "var(--text-secondary)";
        msg.style.maxWidth = "100%";
    } else {
        msg.textContent = text;
    }
    chatMessages.appendChild(msg);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addTyping() {
    const typing = document.createElement("div");
    typing.className = "typing-indicator";
    typing.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';
    chatMessages.appendChild(typing);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return typing;
}

function handleKey(e) {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        if (currentMode === "interview" && questions.length > 0) {
            sendAnswer();
        } else {
            askQuestion();
        }
    }
    autoResize();
}

function autoResize() {
    questionInput.style.height = "auto";
    questionInput.style.height = Math.min(questionInput.scrollHeight, 120) + "px";
}

async function askQuestion() {
    const question = questionInput.value.trim();
    if (!question) return;

    questionInput.value = "";
    questionInput.style.height = "auto";

    const welcome = chatMessages.querySelector(".welcome-message");
    if (welcome) welcome.remove();

    addMessage("user", question);

    const typing = addTyping();

    try {
        const res = await fetch("/api/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question }),
        });
        const data = await res.json();

        typing.remove();

        const assistantMsg = document.createElement("div");
        assistantMsg.className = `message ${data.error ? "error" : "assistant"}`;
        assistantMsg.textContent = data.error || data.answer;

        if (data.sources && data.sources.length > 0) {
            const sourcesDiv = document.createElement("div");
            sourcesDiv.className = "sources";
            sourcesDiv.innerHTML = "📎 " + data.sources.map((s) => `<span>${s.split("/").pop()}</span>`).join("");
            assistantMsg.appendChild(sourcesDiv);
        }

        chatMessages.appendChild(assistantMsg);
    } catch (err) {
        typing.remove();
        addMessage("error", err.message);
    }

    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function toggleSidebar() {
    document.getElementById("sidebar").classList.toggle("collapsed");
}
