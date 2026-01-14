import os
import sys
from pyngrok import ngrok, conf

# Your Auth Token
NGROK_AUTH_TOKEN = "2wwmQzh84l1XV69rYE9rr5HVHVU_5U14VefPMfhSZhzrBir7R"

def start_tunnel():
    print("Initializing ngrok tunnel...")
    
    # 1. Authenticate
    conf.get_default().auth_token = NGROK_AUTH_TOKEN
    
    # 2. Open Tunnel to Flask (Port 5000)
    try:
        public_url = ngrok.connect(5000).public_url
        print("\n" + "="*60)
        print(f"🚀 Tunnelling Active! Your Public URL is:")
        print(f"\n      {public_url}\n")
        print("="*60)
        print("Copy this URL and paste it into Project_APIR_GAS/Code.gs (FLASK_API_URL)")
        print("Press Ctrl+C to stop.")
        
        # Keep process alive
        try:
            # Python 3
            input()
        except NameError:
            pass
            
    except Exception as e:
        print(f"Error starting tunnel: {e}")

if __name__ == "__main__":
    start_tunnel()
