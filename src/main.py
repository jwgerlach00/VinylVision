from PIL import Image
from config import Config
from discogs import Client
from ocr import Ocr
from ai import Llm, Llava

import logging
from config.logging_config import configure_logging
configure_logging()
logger = logging.getLogger(__name__)

TOKEN = Config.discogs_pat
client = Client(TOKEN)

image_path = "src/resources/eagles.jpg"

model = "llm"

if model == "llm":
    image = Image.open(image_path)
    ocr = Ocr()
    extracted_text = ocr.run(image)
    llm = Llm()
    out = llm.get_album_name_and_side(extracted_text)
    logger.info(out)

if model == "llava":
    llava = Llava()
    out = llava.get_album_name_and_side(image_path=image_path)
    logger.info(out)
