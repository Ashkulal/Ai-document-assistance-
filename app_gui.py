import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import threading
from assistant import DocumentAssistant


class AssistantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Document Assistant")
        self.root.geometry("800x600")
        self.assistant = None
        
        self._build_ui()
    
    def _build_ui(self):
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill=tk.X)
        
        ttk.Label(top_frame, text="API Key:").pack(side=tk.LEFT)
        self.api_key_entry = ttk.Entry(top_frame, width=40, show="*")
        self.api_key_entry.pack(side=tk.LEFT, padx=5)
        
        self.load_btn = ttk.Button(top_frame, text="Load Documents", command=self._load_documents)
        self.load_btn.pack(side=tk.LEFT, padx=5)
        
        mid_frame = ttk.Frame(self.root, padding=10)
        mid_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(mid_frame, text="Question:").pack(anchor=tk.W)
        self.question_entry = ttk.Entry(mid_frame, width=80)
        self.question_entry.pack(fill=tk.X, pady=(0, 5))
        self.question_entry.bind("<Return>", lambda e: self._ask_question())
        
        self.ask_btn = ttk.Button(mid_frame, text="Ask", command=self._ask_question)
        self.ask_btn.pack(anchor=tk.W, pady=(0, 10))
        
        ttk.Label(mid_frame, text="Answer:").pack(anchor=tk.W)
        self.answer_text = scrolledtext.ScrolledText(mid_frame, height=15, wrap=tk.WORD)
        self.answer_text.pack(fill=tk.BOTH, expand=True)
        
        bottom_frame = ttk.Frame(self.root, padding=10)
        bottom_frame.pack(fill=tk.X)
        self.status_label = ttk.Label(bottom_frame, text="Ready")
        self.status_label.pack(side=tk.LEFT)
    
    def _load_documents(self):
        files = filedialog.askopenfilenames(
            title="Select Documents",
            filetypes=[("All Supported", "*.pdf *.txt *.csv *.docx"), ("PDF", "*.pdf"), ("Text", "*.txt")],
        )
        if not files:
            return
        
        api_key = self.api_key_entry.get().strip() or None
        
        def load():
            self.status_label.config(text="Loading documents...")
            self.load_btn.config(state=tk.DISABLED)
            try:
                self.assistant = DocumentAssistant(api_key=api_key)
                num_chunks = self.assistant.ingest_documents(list(files))
                self.status_label.config(text=f"Loaded {len(files)} files into {num_chunks} chunks")
            except Exception as e:
                self.status_label.config(text=f"Error: {e}")
            finally:
                self.load_btn.config(state=tk.NORMAL)
        
        threading.Thread(target=load, daemon=True).start()
    
    def _ask_question(self):
        question = self.question_entry.get().strip()
        if not question:
            return
        if not self.assistant:
            self.status_label.config(text="Load documents first")
            return
        
        def ask():
            self.ask_btn.config(state=tk.DISABLED)
            self.answer_text.delete(1.0, tk.END)
            self.answer_text.insert(tk.END, "Thinking...")
            try:
                result = self.assistant.ask(question)
                self.answer_text.delete(1.0, tk.END)
                self.answer_text.insert(tk.END, result["answer"])
            except Exception as e:
                self.answer_text.delete(1.0, tk.END)
                self.answer_text.insert(tk.END, f"Error: {e}")
            finally:
                self.ask_btn.config(state=tk.NORMAL)
        
        threading.Thread(target=ask, daemon=True).start()


def main():
    root = tk.Tk()
    AssistantGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
