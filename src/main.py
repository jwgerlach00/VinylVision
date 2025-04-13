from PIL import Image
import tempfile
from config import Config
from discogs import Client
from ocr import Ocr
from ai import Text, Vision


def preprocess_image(image: Image) -> Image:
    image = Ocr.convert_to_grayscale(image)
    image = Ocr.auto_enhance_contrast(image)
    image = Ocr.binarize(image)
    return image

def save_temp_image(image: Image) -> None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as file:
        file_path = file.name
    image.save(file_path)
    return file_path


if __name__ == "__main__":
    import logging
    from config.logging_config import configure_logging
    configure_logging()
    logger = logging.getLogger(__name__)

    TOKEN = Config.discogs_pat
    client = Client(TOKEN)

    image_path = "src/resources/fleetwood-close.jpg"
    image = Image.open(image_path)
    image = preprocess_image(image)
    image_path = save_temp_image(image)

    model = "vision"

    if model == "text":
        image = Image.open(image_path)
        ocr = Ocr()
        extracted_text = ocr.run(image)
        text_model = Text()
        out = text_model.get_album_name_and_side(extracted_text)
        logger.info(out)

    if model == "vision":
        vision_model = Vision()
        out = vision_model.get_album_name_and_side(image_path=image_path)
        logger.info(out)
