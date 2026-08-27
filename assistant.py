import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate

from document_loader import (
    load_documents,
    split_documents,
    create_vector_store,
    save_vector_store,
    load_vector_store,
)

load_dotenv()

PROMPT_TEMPLATE = """Use the following context to answer the question. If you cannot answer based on the context, say so honestly.

Context:
{context}

Question: {question}

Answer:"""


class DocumentAssistant:
    def __init__(self, api_key: str = None, model_name: str = "gpt-3.5-turbo"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY in .env or pass api_key.")
        
        self.llm = ChatOpenAI(api_key=self.api_key, model_name=model_name, temperature=0)
        self.vector_store = None
        self.qa_chain = None

    def ingest_documents(self, file_paths: list[str], save_path: str = None) -> int:
        """Load, split, and index documents. Returns number of chunks."""
        documents = load_documents(file_paths)
        if not documents:
            raise ValueError("No documents were loaded. Check file paths and formats.")
        
        chunks = split_documents(documents)
        self.vector_store = create_vector_store(chunks, self.api_key)
        
        if save_path:
            save_vector_store(self.vector_store, save_path)
        
        self._setup_qa_chain()
        return len(chunks)

    def load_from_store(self, store_path: str) -> None:
        """Load an existing vector store."""
        self.vector_store = load_vector_store(store_path, self.api_key)
        self._setup_qa_chain()

    def _setup_qa_chain(self) -> None:
        """Set up the Q&A retrieval chain."""
        prompt = PromptTemplate(template=PROMPT_TEMPLATE, input_variables=["context", "question"])
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(search_kwargs={"k": 3}),
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt},
        )

    def ask(self, question: str) -> dict:
        """Ask a question and get an answer with sources."""
        if not self.qa_chain:
            raise ValueError("No documents loaded. Call ingest_documents() or load_from_store() first.")
        
        result = self.qa_chain.invoke({"query": question})
        return {
            "answer": result["result"],
            "sources": [doc.metadata for doc in result.get("source_documents", [])],
        }


def main():
    assistant = DocumentAssistant()

    print("=== AI Document Assistant ===")
    print("Commands:")
    print("  load <file1> <file2> ...  - Load documents")
    print("  ask <question>            - Ask a question")
    print("  quit                      - Exit")
    print()

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("Goodbye!")
            break

        if user_input.lower().startswith("load "):
            files = user_input[5:].split()
            try:
                num_chunks = assistant.ingest_documents(files)
                print(f"Loaded {len(files)} files into {num_chunks} chunks.\n")
            except Exception as e:
                print(f"Error loading documents: {e}\n")

        elif user_input.lower().startswith("ask "):
            question = user_input[4:]
            try:
                result = assistant.ask(question)
                print(f"\nAnswer: {result['answer']}\n")
                if result["sources"]:
                    print("Sources:")
                    for src in result["sources"]:
                        print(f"  - {src.get('source', 'unknown')}")
                    print()
            except Exception as e:
                print(f"Error: {e}\n")

        else:
            print("Unknown command. Use 'load', 'ask', or 'quit'.\n")


if __name__ == "__main__":
    main()
