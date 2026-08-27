import streamlit as st
import os
import tempfile
from assistant import DocumentAssistant

st.set_page_config(
    page_title="AI Document Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp { background: #0e1117; }
    .block-container { padding-top: 2rem; }
    div[data-testid="stChatMessage"] {
        border: 1px solid #333;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.5rem;
    }
    div[data-testid="stSidebar"] {
        background: #1a1d24;
        border-right: 1px solid #333;
    }
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
    }
    h1 { color: #fff !important; }
    h3 { color: #ccc !important; }
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }
    .status-ready { background: #1a4731; color: #4ade80; }
    .status-empty { background: #3b1c1c; color: #f87171; }
</style>
""", unsafe_allow_html=True)

if "assistant" not in st.session_state:
    st.session_state.assistant = None
if "history" not in st.session_state:
    st.session_state.history = []
if "doc_count" not in st.session_state:
    st.session_state.doc_count = 0

with st.sidebar:
    st.markdown("## ⚙️ Configuration")

    api_key = st.text_input("🔑 API Key", type="password", placeholder="sk-or-v1-...")
    base_url = st.text_input("🌐 Base URL", value="https://openrouter.ai/api/v1")

    model = st.selectbox("🤖 Model", [
        "nvidia/nemotron-3-ultra-550b-a55b:free",
        "nvidia/nemotron-3.5-lightning:free",
        "nvidia/nemotron-3-super-120b-a12b:free",
        "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
        "nvidia/nemotron-3-nano-30b-a3b:free",
        "nvidia/nemotron-nano-9b-v2:free",
        "minimax/minimax-m3:free",
        "minimax/minimax-m2.7:free",
        "cohere/north-mini-code:free",
        "poolside/laguna-s-2.1:free",
        "poolside/laguna-xs-2.1:free",
        "dots-studio/dots-3-note-preview:free",
        "thinkingmachines/inkling:free",
        "thinkingmachines/inkling-small:free",
        "z-ai/glm-5.2:free",
        "liquid/lfm-2.5-2.6b:free",
        "google/gemma-4-31b-it:free",
        "google/gemma-4-26b-a4b-it:free",
        "openai/gpt-oss-20b:free",
        "gpt-3.5-turbo",
        "gpt-4",
    ])

    st.divider()
    st.markdown("## 📁 Documents")

    uploaded_files = st.file_uploader(
        "Drop files here",
        type=["pdf", "txt", "csv", "docx"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded_files:
        file_names = [f.name for f in uploaded_files]
        st.caption(f"{len(uploaded_files)} file(s): {', '.join(file_names[:3])}{'...' if len(file_names) > 3 else ''}")

    if st.button("🚀 Process Documents", type="primary", disabled=not uploaded_files):
        with st.spinner("Indexing documents..."):
            temp_dir = tempfile.mkdtemp()
            file_paths = []
            for f in uploaded_files:
                path = os.path.join(temp_dir, f.name)
                with open(path, "wb") as file:
                    file.write(f.getvalue())
                file_paths.append(path)

            try:
                st.session_state.assistant = DocumentAssistant(api_key=api_key, model_name=model, base_url=base_url)
                num_chunks = st.session_state.assistant.ingest_documents(file_paths)
                st.session_state.doc_count = len(uploaded_files)
                st.success(f"✅ Indexed {num_chunks} chunks from {len(uploaded_files)} file(s)")
            except Exception as e:
                st.error(f"❌ {e}")

    st.divider()

    if st.session_state.assistant:
        st.markdown('<span class="status-badge status-ready">● Ready</span>', unsafe_allow_html=True)
        st.caption(f"Model: `{model.split('/')[-1]}`")
        if st.button("🗑️ Clear Chat"):
            st.session_state.history = []
            st.rerun()
    else:
        st.markdown('<span class="status-badge status-empty">● No documents loaded</span>', unsafe_allow_html=True)

st.markdown("## 🧠 AI Document Assistant")
st.caption("Upload documents and ask questions — powered by LangChain + OpenAI")

for role, msg in st.session_state.history:
    with st.chat_message(role, avatar="🧑" if role == "user" else "🤖"):
        st.markdown(msg)

if question := st.chat_input("Ask anything about your documents..."):
    if not st.session_state.assistant:
        st.error("Upload and process documents first.")
    else:
        st.session_state.history.append(("user", question))
        with st.chat_message("user", avatar="🧑"):
            st.markdown(question)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Analyzing..."):
                result = st.session_state.assistant.ask(question)
                answer = result["answer"]
                st.markdown(answer)

                if result["sources"]:
                    with st.expander("📎 Sources"):
                        for src in result["sources"]:
                            st.code(src.get("source", "unknown"), language=None)

        st.session_state.history.append(("assistant", answer))
