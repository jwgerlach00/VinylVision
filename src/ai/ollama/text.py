from typing import Tuple
import ollama
from config import Config


class Text:

    def __init__(self):
        self.model = Config.ollama_text_model

    def get_album_name_and_side(self, vinyl_label_text: str) -> Tuple[str, int]:
        prompt = lambda text: f"""
        Extract the vinyl album name and vinyl side from the following text:

        {text}

        Respond in the format: "Album Name\nn" where n is an integer equal to the vinyl side. Do not include quotes or any other text.
        """
        query = prompt(vinyl_label_text)
        response = self._query(query)
        lines = response.split("\n")
        return lines

    def _query(self, query: str) -> str:
        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": query
                }
            ]
        )
        return response["message"]["content"]
