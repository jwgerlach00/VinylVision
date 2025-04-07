import logging
import os
from dotenv import load_dotenv

load_dotenv()

def configure_logging():
    log_level = os.getenv("LOGGING_LEVEL").upper()

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),  # Log to console
            logging.FileHandler("app.log", mode="a")  # Log to a file
        ]
    )
