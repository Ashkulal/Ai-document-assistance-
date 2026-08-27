import os
import pytest
from unittest.mock import patch, MagicMock
from document_loader import load_documents, split_documents


def test_split_documents():
    from langchain_core.documents import Document
    docs = [Document(page_content="test content " * 100, metadata={"source": "test"})]
    chunks = split_documents(docs, chunk_size=50, chunk_overlap=10)
    assert len(chunks) > 0


def test_load_documents_empty():
    result = load_documents([])
    assert result == []


def test_load_documents_unsupported():
    result = load_documents(["test.xyz"])
    assert result == []


@patch("document_loader.OpenAIEmbeddings")
@patch("document_loader.FAISS")
def test_create_vector_store(mock_faiss, mock_embeddings):
    from document_loader import create_vector_store
    mock_chunks = [MagicMock()]
    create_vector_store(mock_chunks, api_key="test-key")
    mock_faiss.from_documents.assert_called_once()
