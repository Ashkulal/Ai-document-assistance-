import streamlit as st
import os
import tempfile
from assistant import DocumentAssistant

st.set_page_config(page_title="AI Document Assistant", page_icon="📄", layout="wide")
st.title("AI Document Assistant")

if "assistant" not in st.session_state:
    st.session_state.assistant = None
if "history" not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("OpenAI API Key", type="password")
    model = st.selectbox("Model", ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"])
    
    st.header("Upload Documents")
    uploaded_files = st.file_uploader(
        "Drag & drop files here",
        type=["pdf", "txt", "csv", "docx"],
        accept_multiple_files=True,
    )
    
    if uploaded_files and st.button("Process Documents"):
        with st.spinner("Processing..."):
            temp_dir = tempfile.mkdtemp()
            file_paths = []
            for f in uploaded_files:
                path = os.path.join(temp_dir, f.name)
                with open(path, "wb") as file:
                    file.write(f.getvalue())
                file_paths.append(path)
            
            try:
                st.session_state.assistant = DocumentAssistant(api_key=api_key, model_name=model)
                num_chunks = st.session_state.assistant.ingest_documents(file_paths)
                st.success(f"Loaded {len(uploaded_files)} files into {num_chunks} chunks")
            except Exception as e:
                st.error(f"Error: {e}")

st.header("Ask a Question")

for role, msg in st.session_state.history:
    with st.chat_message(role):
        st.write(msg)

if question := st.chat_input("Ask about your documents..."):
    if not st.session_state.assistant:
        st.warning("Upload and process documents first.")
    else:
        st.session_state.history.append(("user", question))
        with st.chat_message("user"):
            st.write(question)
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = st.session_state.assistant.ask(question)
                answer = result["answer"]
                st.write(answer)
                
                if result["sources"]:
                    with st.expander("Sources"):
                        for src in result["sources"]:
                            st.write(f"- {src.get('source', 'unknown')}")
        
        st.session_state.history.append(("assistant", answer))
