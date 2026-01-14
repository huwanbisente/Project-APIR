import os
import secrets
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
from src.pipeline import Pipeline
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
UPLOAD_FOLDER = 'temp_uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Pipeline
# NOTE: Ensure OPENAI_API_KEY is in .env
pipeline = Pipeline(use_mock=False, openai_api_key=os.getenv("OPENAI_API_KEY"))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "Project APIR Pipeline"}), 200

@app.route('/api/parse', methods=['POST'])
def parse_invoice():
    # 1. Check if file is present
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
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
            
            # 4. Clean up
            os.remove(file_path)
            print(f"Cleaned up {file_path}")
            
            # 5. Return result
            # 5. Return result
            # Check if global error (list with one error dict)
            if isinstance(result, list) and len(result) == 1 and "error" in result[0]:
                 # But maybe it's just one failed invoice in a batch?
                 # Let's just return success=False if the ONLY thing returned is a fatal error
                 if "error" in result[0] and len(result[0]) == 1:
                     return jsonify({"success": False, "error": result[0]["error"]}), 500

            return jsonify({"success": True, "data": result}), 200
            
        except Exception as e:
            # Attempt cleanup if failed
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({"success": False, "error": str(e)}), 500
    
    return jsonify({"error": "File type not allowed"}), 400

if __name__ == '__main__':
    # Running on 0.0.0.0 to easily allow local network testing if needed
    app.run(host='0.0.0.0', port=5000, debug=True)
