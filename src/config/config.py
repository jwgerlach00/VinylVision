import os
from dotenv import load_dotenv
load_dotenv()


class _Config:

    def __init__(self):
        self.ollama_text_model: str = "mistral"
        self.ollama_vision_model: str = "llama3.2-vision"
        self.open_ai_vision_model: str = "gpt-4.1-mini"
        self.discogs_pat: str = os.getenv("DISCOGS_PAT")
        self.open_ai_key: str = os.getenv("OPEN_AI_KEY")
