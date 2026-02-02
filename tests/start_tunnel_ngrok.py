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
    # 2. Open Tunnel to Flask (Port 5000) using Static Domain
    try:
        public_url = ngrok.connect(5000, domain="osvaldo-nonenervating-jama.ngrok-free.dev").public_url
        print("\n" + "="*60)
        print(f"🚀 Tunnelling Active! Your STATIC Public URL is:")
        print(f"\n      {public_url}\n")
        print("="*60)
        print("This URL will NOT change properly configured.")
        
        # Keep process alive forever (Daemon mode)
        import time
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("Stopping tunnel...")
        sys.exit(0)
            
    except Exception as e:
        print(f"Error starting tunnel: {e}")

if __name__ == "__main__":
    start_tunnel()
