import os
import secrets
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from src.pipeline import Pipeline
from src.database import DBManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='../frontend')
CORS(app)  # Enable CORS for all routes

# Configuration
UPLOAD_FOLDER = 'temp_uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Services
pipeline = Pipeline(use_mock=False, openai_api_key=os.getenv("OPENAI_API_KEY"))
db = DBManager()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==========================================
# 🌐 FRONTEND ROUTES
# ==========================================

@app.route('/')
def index():
    return send_from_directory('../frontend', 'Index.html')

@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('../frontend/js', path)

@app.route('/css/<path:path>')
def send_css(path):
    return send_from_directory('../frontend/css', path)

# ==========================================
# 🧠 API ROUTES
# ==========================================

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "Project APIR Local"}), 200

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if db.verify_user(email, password):
        return jsonify({"success": True, "email": email})
    return jsonify({"success": False, "error": "Invalid credentials. Default: admin@example.com / admin123"}), 401

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"success": False, "error": "Email and Password required"}), 400

    success, message = db.create_user(email, password)
    if success:
        return jsonify({"success": True})
    return jsonify({"success": False, "error": message}), 400

@app.route('/api/history', methods=['GET'])
def get_history():
    email = request.args.get('email')
    if not email:
        return jsonify({"success": False, "error": "Email required"}), 400
    
    history = db.get_user_history(email)
    return jsonify({"success": True, "history": history})

@app.route('/api/clear', methods=['POST'])
def clear_workspace():
    data = request.json
    email = data.get('email')
    db.clear_workspace(email)
    return jsonify({"success": True})

@app.route('/api/parse', methods=['POST'])
def parse_invoice():
    # 1. Check if file is present
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    email = request.form.get('email', 'anonymous') # Frontend should send this
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        # 2. Save file securely with unique name
        filename = secure_filename(file.filename)
        unique_filename = f"{secrets.token_hex(8)}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        try:
            file.save(file_path)
            print(f"File saved to {file_path}")
            
            # 3. Process with Pipeline
            print("Starting pipeline processing...")
            result = pipeline.process_file(file_path)
            
            # 4. Save to Database (Placeholder Logic)
            # If result is a list (multiple invoices in one PDF), save each
            if isinstance(result, list):
                for item in result:
                    if "error" not in item:
                        db.save_invoice(email, item, file_path)
            elif isinstance(result, dict) and "error" not in result:
                db.save_invoice(email, result, file_path)

            # 5. Clean up (Optional: We might want to keep files in a real app)
            # For now, deleting to save space
            os.remove(file_path)
            
            # 6. Return result
            if isinstance(result, list) and len(result) == 1 and "error" in result[0]:
                 if "error" in result[0] and len(result[0]) == 1:
                     return jsonify({"success": False, "error": result[0]["error"]}), 500

            return jsonify({"success": True, "data": result}), 200
            
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({"success": False, "error": str(e)}), 500
    
    return jsonify({"error": "File type not allowed"}), 400

if __name__ == '__main__':
    # Running on 0.0.0.0 to easily allow local network testing if needed
    app.run(host='0.0.0.0', port=5000, debug=True)
