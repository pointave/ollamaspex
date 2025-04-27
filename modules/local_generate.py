from PyQt5.QtCore import QThread, pyqtSignal
from ollama import chat

class Worker_Local(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    partial = pyqtSignal(str)

    def __init__(self, memory, LLM_API_MODEL, LLM_MODEL_ID):
        super().__init__()
        self.memory = memory
        self.LLM_API_MODEL = LLM_API_MODEL
        self.LLM_MODEL_ID = LLM_MODEL_ID

    def run(self):
        try:
            full_response = ""
            stream = chat(model='gemma3:latest' if self.LLM_MODEL_ID == "" else self.LLM_MODEL_ID,
                          messages=self.memory, stream=True)
            for chunk in stream:
                content = chunk['message']['content']
                if content:
                    self.partial.emit(content)
                    full_response += content
            self.finished.emit(full_response)
        except Exception as e:
            self.error.emit(str(e))
