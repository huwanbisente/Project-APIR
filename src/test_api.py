from src.llm_client import LLMFactory
from dotenv import load_dotenv
import os

load_dotenv()

def test_api():
    print("Testing API connection...")
    api_key = os.getenv("OPENAI_API_KEY")
    print(f"API Key present: {bool(api_key)}")
    print(f"Base URL: {os.getenv('OPENAI_BASE_URL')}")
    print(f"Model: {os.getenv('OPENAI_MODEL')}")

    client = LLMFactory.get_client(provider="openai")
    
    text = """
    Invoice #12345
    Date: 2023-10-01
    Vendor: Test Supply Co.
    Total: $500.00
    """
    
    print("Sending request...")
    result = client.analyze_text(text)
    print("Result:")
    print(result)

if __name__ == "__main__":
    test_api()
