let selectedFiles = [];

const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("fileInput");
const fileList = document.getElementById("fileList");
const processBtn = document.getElementById("processBtn");
const uploadStatus = document.getElementById("uploadStatus");
const statusBadge = document.getElementById("statusBadge");
const chatMessages = document.getElementById("chatMessages");
const questionInput = document.getElementById("questionInput");
const sendBtn = document.getElementById("sendBtn");

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

// Chat
function handleKey(e) {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        askQuestion();
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
    sendBtn.disabled = true;

    // Remove welcome
    const welcome = chatMessages.querySelector(".welcome-message");
    if (welcome) welcome.remove();

    // User message
    const userMsg = document.createElement("div");
    userMsg.className = "message user";
    userMsg.textContent = question;
    chatMessages.appendChild(userMsg);

    // Typing indicator
    const typing = document.createElement("div");
    typing.className = "typing-indicator";
    typing.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';
    chatMessages.appendChild(typing);
    chatMessages.scrollTop = chatMessages.scrollHeight;

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
        const errorMsg = document.createElement("div");
        errorMsg.className = "message error";
        errorMsg.textContent = err.message;
        chatMessages.appendChild(errorMsg);
    }

    chatMessages.scrollTop = chatMessages.scrollHeight;
    sendBtn.disabled = false;
    questionInput.focus();
}

function toggleSidebar() {
    document.getElementById("sidebar").classList.toggle("collapsed");
}
