import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

from document_loader import load_documents, split_documents, get_full_text

load_dotenv()

PROMPT_TEMPLATE = """Use the following context to answer the question. If you cannot answer based on the context, say so honestly.

Context:
{context}

Question: {question}

Answer:"""


class DocumentAssistant:
    def __init__(self, api_key: str = None, model_name: str = "gpt-3.5-turbo", base_url: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required.")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self.llm = ChatOpenAI(api_key=self.api_key, model_name=model_name, temperature=0, base_url=self.base_url, max_tokens=2048)
        self.documents = []
        self.chunks = []
        self.full_text = ""

    def ingest_documents(self, file_paths: list, save_path: str = None) -> int:
        """Load and index documents."""
        self.documents = load_documents(file_paths)
        if not self.documents:
            raise ValueError("No documents were loaded.")
        self.chunks = split_documents(self.documents)
        self.full_text = get_full_text(self.documents)
        return len(self.chunks)

    def _get_relevant_context(self, question: str) -> str:
        """Simple keyword-based context retrieval."""
        q_words = set(question.lower().split())
        scored = []
        for chunk in self.chunks:
            text = chunk.page_content.lower()
            score = sum(1 for w in q_words if w in text)
            scored.append((score, chunk.page_content))
        scored.sort(key=lambda x: x[0], reverse=True)
        context = "\n\n".join(c for _, c in scored[:5])
        return context if context else self.full_text[:3000]

    def ask(self, question: str) -> dict:
        """Ask a question and get an answer."""
        if not self.documents:
            raise ValueError("No documents loaded.")

        max_tokens = 4096
        context = self._get_relevant_context(question)
        prompt = PROMPT_TEMPLATE.format(context=context, question=question)

        while max_tokens >= 256:
            try:
                self.llm.max_tokens = max_tokens
                result = self.llm.invoke(prompt)
                return {"answer": result.content, "sources": []}
            except Exception as e:
                if "402" in str(e) or "max_tokens" in str(e).lower():
                    max_tokens = max_tokens // 2
                    continue
                raise
        raise ValueError("Insufficient credits.")
