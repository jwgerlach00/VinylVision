import os
from dotenv import load_dotenv
load_dotenv()


class _Config:

    def __init__(self):
        # self.ollama_llm_model: str = "gemma2:2b"
        self.ollama_llm_model: str = "mistral"
        self.ollama_llava_model: str = "llava:7b"
        self.discogs_pat = os.getenv("DISCOGS_PAT")
