import pytesseract
from PIL import Image, ImageEnhance


class Ocr:

    @staticmethod
    def convert_to_grayscale(image: Image) -> Image:
        return image.convert("L")

    @staticmethod
    def enhance_contract(image: Image, factor: float) -> Image:
        contrast_enhancer = ImageEnhance.Contrast(image)
        return contrast_enhancer.enhance(factor)

    @staticmethod
    def extract_text(image: Image) -> str:
        # Use Tesseract to do OCR on the image
        return pytesseract.image_to_string(image)
    
    def run(self, image: Image) -> str:
        # Convert to grayscale
        image = self.convert_to_grayscale(image)
        # Enhance contrast
        # self.enhance_contract(image, 2.0)
        # Extract text
        return self.extract_text(image)
