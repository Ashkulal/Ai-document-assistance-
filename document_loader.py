import os
import re
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    CSVLoader,
    Docx2txtLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS


SUPPORTED_EXTENSIONS = {
    ".pdf": PyPDFLoader,
    ".txt": TextLoader,
    ".csv": CSVLoader,
    ".docx": Docx2txtLoader,
}


def clean_text(text: str) -> str:
    """Remove emojis and non-ASCII characters from text."""
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def load_documents(file_paths: list[str]) -> list:
    """Load documents from supported file types."""
    documents = []
    for file_path in file_paths:
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            print(f"Skipping unsupported file: {file_path}")
            continue
        loader = SUPPORTED_EXTENSIONS[ext](file_path)
        docs = loader.load()
        for doc in docs:
            doc.page_content = clean_text(doc.page_content)
            for key in doc.metadata:
                if isinstance(doc.metadata[key], str):
                    doc.metadata[key] = clean_text(doc.metadata[key])
        documents.extend(docs)
    return documents


def split_documents(documents: list, chunk_size: int = 1000, chunk_overlap: int = 200) -> list:
    """Split documents into smaller chunks for processing."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    return text_splitter.split_documents(documents)


def create_vector_store(chunks: list, api_key: str = None) -> FAISS:
    """Create a FAISS vector store from document chunks."""
    embeddings = OpenAIEmbeddings(api_key=api_key)
    vector_store = FAISS.from_documents(chunks, embeddings)
    return vector_store


def save_vector_store(vector_store: FAISS, path: str) -> None:
    """Save vector store to disk."""
    vector_store.save_local(path)


def load_vector_store(path: str, api_key: str = None) -> FAISS:
    """Load vector store from disk."""
    embeddings = OpenAIEmbeddings(api_key=api_key)
    return FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)
