import sqlite3
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = 'local_data.db'

def init_db():
    """Initialize the SQLite database with Users and Invoices tables."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            created_at TEXT
        )
    ''')
    
    # Create Invoices Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            vendor_name TEXT,
            invoice_number TEXT,
            invoice_date TEXT,
            due_date TEXT,
            total_amount REAL,
            tax_amount REAL,
            currency TEXT,
            line_items TEXT,  -- JSON string
            file_path TEXT,
            timestamp TEXT,
            FOREIGN KEY(user_email) REFERENCES users(email)
        )
    ''')
    
    # Seed a default user if empty
    c.execute('SELECT * FROM users WHERE email = ?', ('admin@example.com',))
    if not c.fetchone():
        # Default Pass: admin123
        p_hash = generate_password_hash('admin123')
        c.execute('INSERT INTO users VALUES (?, ?, ?)', 
                 ('admin@example.com', p_hash, datetime.now().isoformat()))
        print("Initialized default user: admin@example.com / admin123")

    conn.commit()
    conn.close()

class DBManager:
    def __init__(self):
        self.db_path = DB_PATH

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        return conn

    def verify_user(self, email, password):
        """Check if user exists and password is correct."""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('SELECT password_hash FROM users WHERE email = ?', (email,))
        row = c.fetchone()
        conn.close()
        
        if row:
            return check_password_hash(row['password_hash'], password)
        return False

    def create_user(self, email, password):
        """Register a new user."""
        conn = self.get_connection()
        c = conn.cursor()
        try:
            # Check exist
            c.execute('SELECT email FROM users WHERE email = ?', (email,))
            if c.fetchone():
                return False, "User already exists"

            # Create
            p_hash = generate_password_hash(password)
            c.execute('INSERT INTO users VALUES (?, ?, ?)', 
                     (email, p_hash, datetime.now().isoformat()))
            conn.commit()
            return True, "User created successfully"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def get_user_history(self, email):
        conn = self.get_connection()
        # Get latest 50
        rows = conn.execute('''
            SELECT * FROM invoices 
            WHERE user_email = ? 
            ORDER BY id DESC LIMIT 50
        ''', (email,)).fetchall()
        conn.close()
        
        history = []
        for row in rows:
            # Convert SQLite Row to Dict
            item = dict(row)
            # Parse JSON line items back to list
            if item.get('line_items'):
                try:
                    item['line_items'] = json.loads(item['line_items'])
                except:
                    item['line_items'] = []
            history.append(item)
        return history

    def save_invoice(self, email, data, file_path=""):
        conn = self.get_connection()
        
        # Serialize line items safely
        line_items_json = json.dumps(data.get('line_items', []))
        
        conn.execute('''
            INSERT INTO invoices (
                user_email, vendor_name, invoice_number, invoice_date, due_date,
                total_amount, tax_amount, currency, line_items, file_path, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            email,
            data.get('vendor_name'),
            data.get('invoice_number'),
            data.get('invoice_date'),
            data.get('due_date'),
            data.get('total_amount', 0),
            data.get('tax_amount', 0),
            data.get('currency', 'USD'),
            line_items_json,
            file_path,
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()

    def clear_workspace(self, email):
        conn = self.get_connection()
        conn.execute('DELETE FROM invoices WHERE user_email = ?', (email,))
        conn.commit()
        conn.close()

# Initialize on module load
init_db()
