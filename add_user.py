import sqlite3
import sys
from datetime import datetime
from werkzeug.security import generate_password_hash

DB_PATH = 'local_data.db'

def create_user(email, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Check if exists
        c.execute('SELECT email FROM users WHERE email = ?', (email,))
        if c.fetchone():
            print(f"Error: User {email} already exists!")
            return

        # Hash Pass
        p_hash = generate_password_hash(password)
        
        # Insert
        c.execute('INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)', 
                 (email, p_hash, datetime.now().isoformat()))
        conn.commit()
        print(f"Success! Created user: {email}")
        
    except Exception as e:
        print(f"Database Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("--- APIR User Creator ---")
    if len(sys.argv) == 3:
        # CLI Mode: python add_user.py email pass
        create_user(sys.argv[1], sys.argv[2])
    else:
        # Interactive Mode
        e = input("Enter Email: ").strip()
        p = input("Enter Password: ").strip()
        if e and p:
            create_user(e, p)
        else:
            print("Email and Password required.")
