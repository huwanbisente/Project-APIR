# Project APIR (AI-Assisted Invoice Processing)

A Hybrid Invoice Processing System that uses Python (Flask + Llama/OpenAI) for intelligence and Google Apps Script for Google Workspace integration.

## Features
- **Dual-Mode UI**: Use either a Local Web Interface or Google Apps Script Web App.
- **Smart Extraction**: Uses LLMs to parse unstructured PDFs/Images into JSON.
- **Google Sheets Sync**: (Mode B) Automatically saves data to Google Sheets.
- **Batch Processing**: CLI tool for bulk processing folders.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Environment Config**:
    Create `.env` and add your keys:
    ```
    OPENAI_API_KEY=sk-...
    ```

## Usage

### 1. Web Application (Flask)
Starts the backend API and Local UI.
```bash
python app.py
```
- Local UI: `http://localhost:5000`
- API Endpoint: `POST /api/parse`

### 2. Google Apps Script Integration
To connect the Cloud frontend (GAS) to your local backend:
1.  Run `ngrok http 5000`.
2.  Update `Project_APIR_GAS/Code.gs` with the ngrok URL.
3.  Deploy the GAS Project.

### 3. Command Line Interface (CLI)
Process a folder of invoices without a UI.
```bash
python -m src.main --input "path/to/invoices"
```
