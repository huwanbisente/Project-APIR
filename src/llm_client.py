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
        print("DEBUG: Executing analyze_text (Final Replacement)")
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
            print(f"DEBUG: RAW LLM RESPONSE START:\n{content}\nDEBUG: RAW LLM RESPONSE END")

            # Validated Extraction Logic (from debug_llm.py)
            import re
            import json
            
            json_objects = []
            
            # Strategy 1: Code Blocks
            code_block_pattern = r"```json\s*([\[\{][\s\S]*?[\]\}])\s*```"
            matches = re.findall(code_block_pattern, content)
            
            if matches:
                 print(f"DEBUG: Found {len(matches)} JSON code blocks.")
                 for match in matches:
                     try:
                         # Attempt to clean trailing commas which often break JSON
                         # simple hack: remove ", }" or ", ]"
                         clean_match = re.sub(r",\s*([\]\}])", r"\1", match)
                         obj = json.loads(clean_match)
                         if isinstance(obj, list):
                             json_objects.extend(obj)
                         else:
                             json_objects.append(obj)
                     except json.JSONDecodeError:
                         pass

            # Strategy 3: Aggressive Fallback (My Patch)
            if not json_objects:
                print("DEBUG: Standard extraction failed. Attempting aggressive fallback search...")
                try:
                    start = content.find('{')
                    end = content.rfind('}')
                    if start != -1 and end != -1:
                        potential_json = content[start:end+1]
                        # Clean trailing commas
                        potential_json = re.sub(r",\s*([\]\}])", r"\1", potential_json)
                        
                        obj = json.loads(potential_json)
                        if isinstance(obj, list):
                            json_objects.extend(obj)
                        else:
                            json_objects.append(obj)
                        print("DEBUG: Successfully extracted JSON via aggressive fallback.")
                except Exception as e:
                    print(f"DEBUG: Fallback search failed: {e}")

            if not json_objects:
                print("=" * 80)
                print("ERROR: No valid JSON objects found!")
                print("RAW RESPONSE (first 1000 chars):")
                print(content[:1000])
                print("\nRAW RESPONSE (last 500 chars):")
                print(content[-500:])
                print("=" * 80)
                return []

            print(f"DEBUG: Recovered {len(json_objects)} invoices.")
            return json_objects

        except Exception as e:
            print(f"Error calling LLM: {e}")
            return []

class LLMFactory:
    @staticmethod
    def get_client(provider: str = "mock", api_key: str = None) -> LLMProvider:
        if provider.lower() == "openai":
            return OpenAIClient(api_key)
        else:
            return MockLLM()
