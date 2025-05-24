from typing import Tuple
from openai import OpenAI

from config import Config


class Vision:
    def __init__(self):
        self.model = Config.open_ai_vision_model
        self.client = OpenAI(api_key=Config.open_ai_key)

    def get_album_name_and_side(self, image_path: str) -> Tuple[str, int]:
        query = """
        This is an image of a vinyl record label, including the "center label" or "vinyl label" area in the middle of the record.
        I need you to extract the vinyl album name and vinyl side from the image.
        The album name is usually at the top of the label, and the vinyl side is usually a number or letter at the bottom.
        If the tracklist is present, it may help you identify the album name and side.
        The text is in English, you may find a lot of irrelevent text also on the label.
        Respond in the format: "Album Name\nn" where n is an integer equal to the vinyl side.
        Do not include quotes or any other text in your response.
        """
        file_id = self._create_file(image_path)
        response = self._query(query, file_id)
        lines = response.split("\n")
        return lines

    def _create_file(self, file_path: str) -> str:
        with open(file_path, "rb") as file_content:
            result = self.client.files.create(
                file=file_content,
                purpose="vision",
            )
            return result.id

    def _query(self, query: str, file_id: str) -> str:
        response = self.client.responses.create(
            model=self.model,
            input=[{  
                "role": "user",
                "content": [
                    {"type": "input_text", "text": query},
                    {
                        "type": "input_image",
                        "file_id": file_id,
                    },
                ],
            }]
        )
        return response.output_text
