import requests
import os

# Configuration
API_URL = "http://localhost:5000/api/parse"
TEST_FILE = "input_data/invoice_test.pdf" # Replace with a real file in your input_data folder

def test_api():
    print(f"Testing API at {API_URL}...")
    
    # 1. Create a dummy file if not exists
    if not os.path.exists(TEST_FILE):
        print(f"Test file {TEST_FILE} not found. Creating a dummy text file...")
        os.makedirs("input_data", exist_ok=True)
        with open("input_data/dummy.txt", "w") as f:
            f.write("Invoice #12345\nDate: 2023-01-01\nTotal: $500.00")
        TEST_FILE_PATH = "input_data/dummy.txt"
    else:
        TEST_FILE_PATH = TEST_FILE

    # 2. Send Request
    try:
        with open(TEST_FILE_PATH, 'rb') as f:
            files = {'file': f}
            response = requests.post(API_URL, files=files)
        
        print(f"Status Code: {response.status_code}")
        print("Response JSON:")
        print(response.json())
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Connection refused. Make sure 'python app.py' is running!")

if __name__ == "__main__":
    test_api()
