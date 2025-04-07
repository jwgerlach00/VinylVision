from typing import Tuple
import ollama
from config import Config


class Llava:

    def __init__(self):
        self.model = Config.ollama_llava_model

    def get_album_name_and_side(self, image_path: str) -> Tuple[str, int]:
        query = f"""
        This is an image of a vinyl record label, including the "center label" or "vinyl label" area in the middle of the record.
        I need you to extract the vinyl album name and vinyl side from the image.
        The album name is usually at the top of the label, and the vinyl side is usually a number or letter at the bottom.
        If the tracklist is present, it may help you identify the album name and side.
        The text is in English, you may find a lot of irrelevent text also on the label.
        Respond in the format: "Album Name\nn" where n is an integer equal to the vinyl side.
        Do not include quotes or any other text in your response.
        """
        response = self._query(query, image_path)
        lines = response.split("\n")
        return lines
        # album_name: str = lines[0].strip()
        # vinyl_side: str = lines[1].strip()
        # return album_name, int(vinyl_side)

    def _query(self, query: str, image_path: str) -> str:
        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": query,
                    "images": [image_path]
                }
            ]
        )
        return response["message"]["content"]
