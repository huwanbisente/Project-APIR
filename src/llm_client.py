import os
import json
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from src.schema import InvoiceData

class LLMProvider(ABC):
    @abstractmethod
    def analyze_text(self, text: str) -> list[Dict[str, Any]]:
        pass

class MockLLM(LLMProvider):
    def analyze_text(self, text: str) -> list[Dict[str, Any]]:
        print("MOCK LLM: Returning dummy data.")
        return [{
            "vendor_name": "Mock Vendor Inc.",
            "invoice_number": "MOCK-12345",
            "invoice_date": "2023-01-01",
            "due_date": "2023-01-31",
            "tax_amount": 10.0,
            "total_amount": 110.0,
            "currency": "USD",
            "line_items": [
                {"description": "Mock Item 1", "quantity": 1, "unit_price": 50.0, "amount": 50.0},
                {"description": "Mock Item 2", "quantity": 1, "unit_price": 50.0, "amount": 50.0}
            ]
        }]

class OpenAIClient(LLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        try:
            from openai import OpenAI
            base_url = os.getenv("OPENAI_BASE_URL")
            self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
            
            self.client = OpenAI(
                api_key=api_key or os.getenv("OPENAI_API_KEY"),
                base_url=base_url
            )
        except ImportError:
            raise ImportError("OpenAI package not installed. Please run `pip install openai`")
            
    def analyze_text(self, text: str) -> list[Dict[str, Any]]:
        system_prompt = """
        You are an expert invoice data extractor. 
        Your task is to extract structured data from the provided invoice text.
        
        IMPORTANT RULES:
        1. **Invoice Number**: Look specifically for a "Ref" or "Reference" header. The value often starts with "PO-". If found, trace it to the 'invoice_number' field.
        2. **Dates**: Standardize all dates to YYYY-MM-DD.
        3. **Missing Info**: If a field is not found, return null or empty string, do not make up data.
        
        Return ONLY valid JSON complying with the following schema:
        {
            "vendor_name": "string",
            "invoice_number": "string",
            "invoice_date": "YYYY-MM-DD",
            "due_date": "YYYY-MM-DD",
            "tax_amount": float,
            "total_amount": float,
            "currency": "USD",
            "line_items": [
                {"description": "string", "quantity": float, "unit_price": float, "amount": float}
            ]
        }
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Invoice Text:\n{text}"}
                ]
            )
            content = response.choices[0].message.content
            print(f"DEBUG: RAW LLM RESPONSE:\n{content[:500]}...") # Print first 500 chars

            # Robust JSON Extraction using Regex
            # The LLM might return multiple JSON blocks or a list.
            import re
            
            # Look for JSON objects {...}
            # This regex matches balanced braces approximately (non-nested usually works for simple LLM output)
            # or simply extract content between ```json ... ``` code blocks
            
            json_objects = []
            
            # Strategy 1: Extract from Code Blocks (Most reliable for this LLM output)
            # Match either {...} OR [...] inside code blocks
            code_block_pattern = r"```json\s*([\[\{][\s\S]*?[\]\}])\s*```"
            matches = re.findall(code_block_pattern, content)
            
            if matches:
                print(f"DEBUG: Found {len(matches)} JSON code blocks.")
                for match in matches:
                    try:
                        obj = json.loads(match)
                        if isinstance(obj, list):
                            json_objects.extend(obj)
                        else:
                            json_objects.append(obj)
                    except json.JSONDecodeError:
                        pass
            
            # Strategy 2: If no code blocks, look for raw JSON objects/lists
            if not json_objects:
                # Try finding a top-level list [...]
                list_pattern = r"(\[[\s\S]*\])"
                list_match = re.search(list_pattern, content)
                if list_match:
                    try:
                        obj = json.loads(list_match.group(1))
                        if isinstance(obj, list):
                            json_objects.extend(obj)
                    except json.JSONDecodeError:
                        pass
                
                # If still nothing, look for finding individual objects {...}
                if not json_objects:
                    raw_pattern = r"(\{[\s\S]*?\})"
                    potential_matches = re.findall(raw_pattern, content)
                    for match in potential_matches:
                        try:
                            obj = json.loads(match)
                            # Basic validation to filter out non-invoice JSON
                            if isinstance(obj, dict) and "total_amount" in obj:
                                 json_objects.append(obj)
                        except json.JSONDecodeError:
                            pass

            if not json_objects:
                print("Error: No valid JSON objects found in response.")
                return {}

            # NORMALIZATION:
            # We found multiple invoices. 
            print(f"DEBUG: Recovered {len(json_objects)} invoices.")
            
            return json_objects
        except Exception as e:
            print(f"Error calling LLM: {e}")
            if 'content' in locals():
                 print(f"Failed Content: {content}")
            return []

class LLMFactory:
    @staticmethod
    def get_client(provider: str = "mock", api_key: str = None) -> LLMProvider:
        if provider.lower() == "openai":
            return OpenAIClient(api_key)
        else:
            return MockLLM()
