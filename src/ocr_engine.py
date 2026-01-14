import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import os
from typing import List

# NOTE: Ensure Tesseract-OCR is installed on the system and in PATH.
# If not in PATH, uncomment and set the line below:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class OCREngine:
    def __init__(self, tesseract_cmd: str = None):
         if tesseract_cmd:
             pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    
    def extract_text_from_image(self, image_path: str) -> str:
        """Extracts text from a single image file."""
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            print(f"Error processing image {image_path}: {e}")
            return ""

    def convert_pdf_to_images(self, pdf_path: str) -> List[Image.Image]:
        """Converts a PDF to a list of PIL Images."""
        try:
            # poppler_path might need to be configured for Windows if not in PATH
            # e.g., poppler_path=r'C:\Program Files\poppler-xx\bin'
            images = convert_from_path(pdf_path) 
            return images
        except Exception as e:
            print(f"Error converting PDF {pdf_path}: {e}")
            return []

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extracts text from a PDF. Tries native text extraction first, then falls back to OCR."""
        # Method 1: Native Extraction (pypdf)
        try:
            from pypdf import PdfReader
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            if text.strip():
                return text
        except Exception as e:
            print(f"Native extraction failed for {pdf_path}: {e}")

        # Method 2: OCR (pdf2image + pytesseract)
        print(f"Native extraction empty or failed. Attempting OCR for {pdf_path}...")
        try:
            images = self.convert_pdf_to_images(pdf_path)
            full_text = ""
            for i, img in enumerate(images):
                text = pytesseract.image_to_string(img)
                full_text += f"\n--- Page {i+1} ---\n{text}"
            return full_text
        except Exception as e:
             print(f"OCR failed for {pdf_path}. Ensure Poppler and Tesseract are installed. Error: {e}")
             return ""

    def extract_text_from_scanned_pdf(self, pdf_path: str) -> str:
        """Alias for extract_text_from_pdf for clarity in pipeline."""
        return self.extract_text_from_pdf(pdf_path)
