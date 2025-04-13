import os
from dotenv import load_dotenv
load_dotenv()


class _Config:

    def __init__(self):
        self.ollama_text_model: str = "mistral"
        self.ollama_vision_model: str = "llama3.2-vision"
        self.discogs_pat = os.getenv("DISCOGS_PAT")
