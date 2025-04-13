import pytesseract
from PIL import Image, ImageEnhance, ImageOps


class Ocr:

    @staticmethod
    def convert_to_grayscale(image: Image) -> Image:
        return image.convert("L")

    @staticmethod
    def enhance_contract(image: Image, factor: float) -> Image:
        contrast_enhancer = ImageEnhance.Contrast(image)
        return contrast_enhancer.enhance(factor)
    
    @staticmethod
    def auto_enhance_contrast(image: Image) -> Image:
        return ImageOps.autocontrast(image)
    
    @staticmethod
    def binarize(image: Image) -> Image:
        threshold = 128 # 256/2 for binary
        return image.point(lambda x: 0 if x < threshold else 255, '1')

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
