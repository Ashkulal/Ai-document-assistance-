import os
import re
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    CSVLoader,
    Docx2txtLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_documents(file_paths: list) -> list:
    """Load documents from file paths."""
    loaders = {
        ".pdf": PyPDFLoader,
        ".txt": TextLoader,
        ".csv": CSVLoader,
        ".docx": Docx2txtLoader,
    }
    documents = []
    for path in file_paths:
        ext = os.path.splitext(path)[1].lower()
        loader_cls = loaders.get(ext)
        if loader_cls:
            try:
                docs = loader_cls(path).load()
                for doc in docs:
                    doc.page_content = re.sub(r'[^\x00-\x7F]+', ' ', doc.page_content)
                    doc.page_content = re.sub(r'\s+', ' ', doc.page_content).strip()
                documents.extend(docs)
            except Exception as e:
                print(f"Error loading {path}: {e}")
    return documents


def split_documents(documents: list) -> list:
    """Split documents into chunks."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return splitter.split_documents(documents)


def get_full_text(documents: list) -> str:
    """Get full text from all documents."""
    return "\n\n".join(d.page_content for d in documents)
