let selectedFiles = [];
let currentMode = "chat";
let currentRound = null;
let questions = [];
let currentQuestionIndex = 0;
let totalScore = 0;
let totalAnswered = 0;
let answers = {};
let isRecording = false;
let recognition = null;
let timerInterval = null;
let seconds = 0;
let codingProblem = null;

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

// Models
document.getElementById("apiKey").addEventListener("keydown", (e) => {
    if (e.key === "Enter") fetchModels();
});

async function fetchModels() {
    const baseUrl = document.getElementById("baseUrl").value;
    const apiKey = document.getElementById("apiKey").value;
    const modelSelect = document.getElementById("modelSelect");
    const modelStatus = document.getElementById("modelStatus");
    const fetchBtn = document.getElementById("fetchBtn");

    if (!apiKey) { modelStatus.className = "status error"; modelStatus.textContent = "Enter API key first"; return; }

    fetchBtn.disabled = true; fetchBtn.textContent = "Loading...";
    modelStatus.className = "status"; modelStatus.textContent = "Fetching models...";
    modelSelect.innerHTML = '<option value="">Loading...</option>';

    try {
        const res = await fetch("/api/models", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ base_url: baseUrl, api_key: apiKey }) });
        const data = await res.json();
        if (data.error) { modelSelect.innerHTML = '<option value="">Failed</option>'; modelStatus.className = "status error"; modelStatus.textContent = data.error; return; }
        modelSelect.innerHTML = "";
        data.models.forEach(m => { const opt = document.createElement("option"); opt.value = m.id; opt.textContent = `${m.name} (${m.ctx})`; modelSelect.appendChild(opt); });
        modelStatus.className = "status success"; modelStatus.textContent = `${data.models.length} models loaded`;
    } catch (err) { modelSelect.innerHTML = '<option value="">Failed</option>'; modelStatus.className = "status error"; modelStatus.textContent = err.message; }
    fetchBtn.disabled = false; fetchBtn.textContent = "Fetch";
}

// Voice
if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SR(); recognition.continuous = false; recognition.interimResults = true; recognition.lang = "en-US";
    recognition.onresult = (e) => { let t = ""; for (let i = e.resultIndex; i < e.results.length; i++) t += e.results[i][0].transcript; questionInput.value = t; };
    recognition.onend = () => { isRecording = false; document.getElementById("voiceBtn").classList.remove("recording"); };
    recognition.onerror = () => { isRecording = false; document.getElementById("voiceBtn").classList.remove("recording"); };
}

function toggleVoice() {
    if (!recognition) { alert("Use Chrome for voice"); return; }
    if (isRecording) { recognition.stop(); isRecording = false; document.getElementById("voiceBtn").classList.remove("recording"); }
    else { recognition.start(); isRecording = true; document.getElementById("voiceBtn").classList.add("recording"); }
}

// Dropzone
dropzone.addEventListener("click", () => fileInput.click());
dropzone.addEventListener("dragover", (e) => { e.preventDefault(); dropzone.classList.add("dragover"); });
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
dropzone.addEventListener("drop", (e) => { e.preventDefault(); dropzone.classList.remove("dragover"); addFiles(e.dataTransfer.files); });
fileInput.addEventListener("change", (e) => addFiles(e.target.files));

function addFiles(files) { for (const f of files) { if (!selectedFiles.find(s => s.name === f.name)) selectedFiles.push(f); } renderFiles(); }
function removeFile(name) { selectedFiles = selectedFiles.filter(f => f.name !== name); renderFiles(); }
function renderFiles() { fileList.innerHTML = selectedFiles.map(f => `<div class="file-item"><span class="name">${f.name}</span><button class="remove" onclick="removeFile('${f.name}')">×</button></div>`).join(""); processBtn.disabled = selectedFiles.length === 0; }

// Upload
async function uploadFiles() {
    const apiKey = document.getElementById("apiKey").value;
    const baseUrl = document.getElementById("baseUrl").value;
    const model = document.getElementById("modelSelect").value;
    if (!apiKey) { uploadStatus.className = "status error"; uploadStatus.textContent = "Enter API key first"; return; }
    processBtn.disabled = true; uploadStatus.className = "status"; uploadStatus.textContent = "Uploading & analyzing...";

    const formData = new FormData();
    formData.append("api_key", apiKey); formData.append("base_url", baseUrl); formData.append("model", model);
    selectedFiles.forEach(f => formData.append("files", f));

    try {
        const res = await fetch("/api/upload", { method: "POST", body: formData });
        const data = await res.json();
        if (data.success) {
            uploadStatus.className = "status success";
            uploadStatus.textContent = `✅ Resume processed — ${data.chunks} chunks indexed`;
            statusBadge.className = "status-badge ready"; statusBadge.textContent = "● Ready";
            sendBtn.disabled = false; questionInput.focus();
            showWelcome(data.resume_name, data.resume_preview);
        } else { uploadStatus.className = "status error"; uploadStatus.textContent = `❌ ${data.error}`; }
    } catch (err) { uploadStatus.className = "status error"; uploadStatus.textContent = `❌ ${err.message}`; }
    processBtn.disabled = false;
}

function showWelcome(name, preview) {
    const welcome = document.getElementById("welcomeMessage");
    if (welcome) welcome.remove();
    const w = document.createElement("div");
    w.className = "welcome-message";
    w.innerHTML = `
        <div class="welcome-icon">✅</div>
        <h3>Resume Loaded: ${name}</h3>
        <p class="resume-preview">${preview}...</p>
        <h4 style="margin-top:1.5rem;">Choose a round to start:</h4>
        <div class="features-grid">
            <div class="feature clickable" onclick="setMode('interview');startMCQ('aptitude')">📝 30 Aptitude MCQs</div>
            <div class="feature clickable" onclick="setMode('interview');startMCQ('technical')">💻 30 Technical MCQs</div>
            <div class="feature clickable" onclick="setMode('interview');startCoding()">⌨️ Coding Challenge</div>
            <div class="feature clickable" onclick="setMode('chat')">💬 Ask Anything</div>
        </div>`;
    chatMessages.appendChild(w);
}

// Mode
function setMode(mode) {
    currentMode = mode;
    document.getElementById("chatMode").classList.toggle("active", mode === "chat");
    document.getElementById("interviewMode").classList.toggle("active", mode === "interview");
    document.getElementById("interviewPanel").style.display = mode === "interview" ? "block" : "none";
    if (mode === "chat") endRound();
}

// Timer
function startTimer() { seconds = 0; document.getElementById("timer").textContent = "00:00"; timerInterval = setInterval(() => { seconds++; const m = String(Math.floor(seconds / 60)).padStart(2, "0"); const s = String(seconds % 60).padStart(2, "0"); document.getElementById("timer").textContent = `${m}:${s}`; }, 1000); }
function stopTimer() { clearInterval(timerInterval); }

// MCQ Round
async function startMCQ(roundType) {
    if (statusBadge.textContent.includes("No documents")) { alert("Upload a resume first!"); return; }

    currentRound = roundType;
    questions = []; currentQuestionIndex = 0; totalScore = 0; totalAnswered = 0; answers = {};

    document.getElementById("roundSelector").style.display = "none";
    document.getElementById("activeRound").style.display = "flex";
    document.getElementById("progressBar").style.display = "block";
    scoreDisplay.style.display = "block";

    const names = { aptitude: "📝 Aptitude (30 Q)", technical: "💻 Technical (30 Q)" };
    document.getElementById("roundBadge").textContent = names[roundType];

    const welcome = chatMessages.querySelector(".welcome-message");
    if (welcome) welcome.remove();
    addMessage("system", `Generating ${roundType} questions from your resume...`);

    const typing = addTyping();

    try {
        const res = await fetch("/api/mcq", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ round_type: roundType, count: 30 }) });
        const data = await res.json();
        typing.remove();
        if (data.error) { addMessage("error", data.error); endRound(); return; }

        questions = data.questions;
        if (!questions.length) { addMessage("error", "No questions generated"); endRound(); return; }

        startTimer();
        showMCQ(0);
    } catch (err) { typing.remove(); addMessage("error", err.message); endRound(); }
}

function showMCQ(index) {
    if (index >= questions.length) { finishMCQ(); return; }
    currentQuestionIndex = index;

    document.getElementById("questionCounter").textContent = `Q${index + 1}/${questions.length}`;
    const pct = ((index) / questions.length) * 100;
    document.getElementById("progressFill").style.width = `${pct}%`;

    const q = questions[index];
    const answered = answers[index] !== undefined;

    const card = document.createElement("div");
    card.className = "mcq-card";
    card.id = `mcq-${index}`;
    card.innerHTML = `
        <div class="mcq-question"><span class="q-num">Q${index + 1}</span> ${q.q}</div>
        <div class="mcq-options">
            ${["A", "B", "C", "D"].map(opt => `
                <button class="mcq-option ${answered && answers[index] === opt ? 'selected' : ''}" 
                    onclick="selectOption(${index}, '${opt}')" ${answered ? 'disabled' : ''}>
                    <span class="opt-letter">${opt}</span>
                    <span class="opt-text">${q[opt]}</span>
                </button>
            `).join("")}
        </div>
        ${answered ? `<div class="mcq-feedback ${answers[index] === q.answer ? 'correct' : 'wrong'}">
            ${answers[index] === q.answer ? '✅ Correct!' : `❌ Wrong — Answer: ${q.answer}`}
            <div class="explanation">${q.explanation}</div>
        </div>` : ''}
    `;
    chatMessages.appendChild(card);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function selectOption(qIndex, option) {
    if (answers[qIndex] !== undefined) return;
    answers[qIndex] = option;

    const q = questions[qIndex];
    const isCorrect = option === q.answer;
    if (isCorrect) totalScore++;
    totalAnswered++;

    const card = document.getElementById(`mcq-${qIndex}`);
    card.querySelectorAll(".mcq-option").forEach(btn => {
        btn.disabled = true;
        const letter = btn.querySelector(".opt-letter").textContent;
        if (letter === q.answer) btn.classList.add("correct");
        if (letter === option && !isCorrect) btn.classList.add("wrong");
    });

    const feedback = document.createElement("div");
    feedback.className = `mcq-feedback ${isCorrect ? 'correct' : 'wrong'}`;
    feedback.innerHTML = `${isCorrect ? '✅ Correct!' : `❌ Wrong — Answer: ${q.answer}`}<div class="explanation">${q.explanation}</div>`;
    card.appendChild(feedback);

    const avg = totalAnswered > 0 ? ((totalScore / totalAnswered) * 100).toFixed(0) : 0;
    scoreValue.textContent = `${avg}%`;
    scoreValue.style.color = avg >= 70 ? "#22c55e" : avg >= 50 ? "#f59e0b" : "#ef4444";

    setTimeout(() => {
        if (currentQuestionIndex === qIndex) showMCQ(qIndex + 1);
    }, 800);
}

function finishMCQ() {
    stopTimer();
    const pct = totalAnswered > 0 ? ((totalScore / totalAnswered) * 100).toFixed(0) : 0;
    const grade = pct >= 90 ? "A+" : pct >= 80 ? "A" : pct >= 70 ? "B+" : pct >= 60 ? "B" : pct >= 50 ? "C" : "D";

    document.getElementById("progressFill").style.width = "100%";

    const summary = document.createElement("div");
    summary.className = "mcq-summary";
    summary.innerHTML = `
        <h3>🎉 Round Complete!</h3>
        <div class="summary-score" style="color:${pct >= 70 ? '#22c55e' : '#f59e0b'}">${pct}%</div>
        <div class="summary-grade">Grade: ${grade}</div>
        <div class="summary-details">
            <span>✅ ${totalScore} correct</span>
            <span>❌ ${totalAnswered - totalScore} wrong</span>
            <span>📝 ${totalAnswered}/${questions.length} answered</span>
            <span>⏱️ ${document.getElementById("timer").textContent}</span>
        </div>
        <div class="summary-actions">
            <button class="btn-primary" onclick="retryRound()">🔄 Retry</button>
            <button class="btn-primary" onclick="endRound()">← Back to Rounds</button>
        </div>
    `;
    chatMessages.appendChild(summary);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function retryRound() {
    const round = currentRound;
    endRound();
    if (round === "aptitude" || round === "technical") startMCQ(round);
}

// Coding Round
async function startCoding() {
    if (statusBadge.textContent.includes("No documents")) { alert("Upload a resume first!"); return; }

    currentRound = "coding";
    document.getElementById("roundSelector").style.display = "none";
    document.getElementById("activeRound").style.display = "flex";
    document.getElementById("progressBar").style.display = "none";
    scoreDisplay.style.display = "none";
    document.getElementById("roundBadge").textContent = "⌨️ Coding Challenge";
    document.getElementById("questionCounter").textContent = "";

    const welcome = chatMessages.querySelector(".welcome-message");
    if (welcome) welcome.remove();
    addMessage("system", "Generating coding problem based on your resume...");

    const typing = addTyping();

    try {
        const res = await fetch("/api/coding", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ difficulty: "medium" }) });
        const data = await res.json();
        typing.remove();
        if (data.error) { addMessage("error", data.error); endRound(); return; }

        codingProblem = data.problem;
        showCodingProblem();
    } catch (err) { typing.remove(); addMessage("error", err.message); endRound(); }
}

function showCodingProblem() {
    const p = codingProblem;
    const card = document.createElement("div");
    card.className = "coding-card";
    card.innerHTML = `
        <div class="coding-title">⌨️ ${p.title}</div>
        <div class="coding-desc">${p.description}</div>
        <div class="coding-section">
            <strong>Examples:</strong>
            ${p.examples.map((ex, i) => `
                <div class="coding-example">
                    <div><strong>Input:</strong> <code>${ex.input}</code></div>
                    <div><strong>Output:</strong> <code>${ex.output}</code></div>
                    <div class="explanation">${ex.explanation}</div>
                </div>
            `).join("")}
        </div>
        <div class="coding-section"><strong>Constraints:</strong> ${p.constraints}</div>
        <div class="coding-section">
            <strong>Test Cases:</strong>
            ${p.test_cases.map((tc, i) => `
                <div class="test-case">Test ${i + 1}: Input <code>${tc.input}</code> → Expected <code>${tc.output}</code></div>
            `).join("")}
        </div>
        <div class="coding-editor">
            <div class="editor-header">
                <span>📝 Your Solution (${p.language})</span>
                <button class="run-btn" onclick="runCode()">▶ Run Tests</button>
            </div>
            <textarea id="codeEditor" class="code-textarea" spellcheck="false">${p.starter_code}</textarea>
        </div>
        <div id="codeResults"></div>
    `;
    chatMessages.appendChild(card);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function runCode() {
    const code = document.getElementById("codeEditor").value;
    const p = codingProblem;
    const results = document.getElementById("codeResults");

    let passed = 0;
    let total = p.test_cases.length;
    let html = '<div class="test-results"><strong>Test Results:</strong>';

    p.test_cases.forEach((tc, i) => {
        try {
            let output = "";
            if (p.language === "python") {
                const fn = new Function("return " + code)();
                output = String(fn(tc.input));
            } else {
                output = "Run locally to test";
            }
            const pass = output.trim() === tc.output.trim();
            if (pass) passed++;
            html += `<div class="test-result ${pass ? 'pass' : 'fail'}">
                Test ${i + 1}: ${pass ? '✅ PASS' : `❌ FAIL — Got: ${output}`}
            </div>`;
        } catch (e) {
            html += `<div class="test-result fail">Test ${i + 1}: ❌ Error — ${e.message}</div>`;
        }
    });

    html += `<div class="test-summary">${passed}/${total} test cases passed</div></div>`;
    results.innerHTML = html;
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Chat mode
function setMode(mode) {
    currentMode = mode;
    document.getElementById("chatMode").classList.toggle("active", mode === "chat");
    document.getElementById("interviewMode").classList.toggle("active", mode === "interview");
    document.getElementById("interviewPanel").style.display = mode === "interview" ? "block" : "none";
    if (mode === "chat") endRound();
}

async function sendChat() {
    const question = questionInput.value.trim();
    if (!question) return;
    questionInput.value = ""; questionInput.style.height = "auto";
    const welcome = chatMessages.querySelector(".welcome-message");
    if (welcome) welcome.remove();
    addMessage("user", question);
    const typing = addTyping();
    try {
        const res = await fetch("/api/ask", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question }) });
        const data = await res.json();
        typing.remove();
        const msg = document.createElement("div");
        msg.className = `message ${data.error ? "error" : "assistant"}`;
        msg.textContent = data.error || data.answer;
        chatMessages.appendChild(msg);
    } catch (err) { typing.remove(); addMessage("error", err.message); }
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function handleKey(e) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendChat(); }
    questionInput.style.height = "auto";
    questionInput.style.height = Math.min(questionInput.scrollHeight, 120) + "px";
}

function endRound() {
    stopTimer();
    currentRound = null; questions = []; currentQuestionIndex = 0; answers = {};
    document.getElementById("activeRound").style.display = "none";
    document.getElementById("progressBar").style.display = "none";
    document.getElementById("roundSelector").style.display = "flex";
}

// Helpers
function addMessage(type, text) {
    const msg = document.createElement("div");
    msg.className = `message ${type}`;
    if (type === "system") { msg.innerHTML = `<em>${text}</em>`; msg.style.textAlign = "center"; msg.style.color = "var(--text-secondary)"; msg.style.maxWidth = "100%"; }
    else { msg.textContent = text; }
    chatMessages.appendChild(msg);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addTyping() {
    const t = document.createElement("div"); t.className = "typing-indicator";
    t.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';
    chatMessages.appendChild(t); chatMessages.scrollTop = chatMessages.scrollHeight;
    return t;
}

function toggleSidebar() { document.getElementById("sidebar").classList.toggle("collapsed"); }
