import os
import json
import pandas as pd
from typing import Dict, Any
from src.ocr_engine import OCREngine
from src.llm_client import LLMFactory
from src.schema import InvoiceData

class Pipeline:
    def __init__(self, use_mock: bool = False, openai_api_key: str = None):
        self.ocr = OCREngine()
        self.llm = LLMFactory.get_client(provider="mock" if use_mock else "openai", api_key=openai_api_key)

    def process_file(self, file_path: str) -> list[Dict[str, Any]]:
        print(f"Processing file: {file_path}")
        
        # 1. Extraction
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Simple logic: If PDF, convert and OCR. If Image, OCR directly.
        # Ideally, check if PDF has text layer first, but forcing OCR for PoC robustness for "scanned" docs.
        ext = os.path.splitext(file_path)[1].lower()
        extracted_text = ""
        
        if ext == ".pdf":
            print("Detected PDF. Running OCR...")
            extracted_text = self.ocr.extract_text_from_pdf(file_path)
        elif ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
            print("Detected Image. Running OCR...")
            extracted_text = self.ocr.extract_text_from_image(file_path)
        else:
             print(f"Unsupported file type: {ext}. Trying simple text read...")
             try:
                 with open(file_path, 'r', encoding='utf-8') as f:
                     extracted_text = f.read()
             except Exception:
                 return [{"error": "Unsupported file and cannot read as text."}]

        if not extracted_text.strip():
            print("Warning: No text extracted.")
            return [{"error": "No text extracted"}]

        print(f"Extracted {len(extracted_text)} characters.")
        
        # 2. Analysis
        print("Sending to AI...")
        raw_json_list = self.llm.analyze_text(extracted_text)
        
        # 3. Validation
        valid_invoices = []
        if not raw_json_list:
             valid_invoices.append({"error": "No invoices found by AI", "raw_text": extracted_text[:100]})
        
        print(f"DEBUG: Pipeline received {len(raw_json_list)} items from LLM.")
        
        for raw_json in raw_json_list:
            try:
                invoice = InvoiceData(**raw_json)
                valid_invoices.append(invoice.model_dump())
            except Exception as e:
                print(f"Validation Error: {e}")
                valid_invoices.append({"error": str(e), "raw_json": raw_json})
        
        print(f"DEBUG: Pipeline returning {len(valid_invoices)} items.")
        return valid_invoices

    def save_to_json(self, data_list: list, output_path: str):
        """Saves the raw list of dictionaries to a JSON file."""
        if not data_list:
            print("No data to save to JSON.")
            return
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data_list, f, indent=4, default=str)
            print(f"Saved JSON results to {output_path}")
        except Exception as e:
            print(f"Error saving JSON: {e}")

    def save_to_csv(self, data_list: list, output_path: str):
        if not data_list:
            print("No data to save.")
            return

        # Flatten logic: duplicate invoice header for each line item
        flat_data = []
        for invoice in data_list:
            if "error" in invoice:
                continue
                
            header = {k: v for k, v in invoice.items() if k != "line_items"}
            if not invoice.get("line_items"):
                 flat_data.append(header)
            else:
                for item in invoice["line_items"]:
                    row = header.copy()
                    row.update(item)
                    flat_data.append(row)
        
        if not flat_data:
            print("No valid data to write to CSV.")
            return

        df = pd.DataFrame(flat_data)
        df.to_csv(output_path, index=False)
        print(f"Saved results to {output_path}")
