# AI Document Assistant

A Python-based assistant that uses LangChain and OpenAI API to answer questions over uploaded documents.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create `.env` file with your API key:
   ```
   OPENAI_API_KEY=your_key_here
   ```

3. Run the assistant:
   ```bash
   python assistant.py
   ```

## Usage

- `load file1.pdf file2.txt` - Load documents (supports PDF, TXT, CSV, DOCX)
- `ask your question here` - Ask a question about loaded documents
- `quit` - Exit

## Architecture

- `document_loader.py` - Document loading, chunking, and vector store management
- `assistant.py` - Main application with Q&A chain using RetrievalQA
