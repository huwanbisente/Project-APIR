<h1 align="center">Invoice AI Hub</h1>

<p align="center">
  A Hybrid Invoice Processing System harnessing Local LLMs for intelligence and Google Workspace for seamless integration.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Author-Jan%20Vincent%20Chioco-red?style=flat-square" alt="Author">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Stack-Flask%20%2B%20GAS-yellow?style=flat-square" alt="Stack">
  <img src="https://img.shields.io/badge/AI-Llama%203.3-purple?style=flat-square" alt="AI">
</p>

---

*   If you find this tool useful for automating your finance workflows, please consider giving it a star!

**Invoice AI Hub** is a powerful ETL pipeline that ingests unstructured invoice data (PDFs/Images), extracts structured financial information using Local LLMs (Ollama/Llama 3.3) or OpenAI, and automatically synchronizes the results to your Google Sheets. It features a robust multi-tenant architecture with a Google Apps Script frontend.

---

## Features

*   **Dual-Mode Interface**: Operate via a robust Google Apps Script Web App or a local Flask UI.
*   **Intelligent Extraction**: Uses advanced LLMs to parse complex tables and handwritten text with high accuracy.
*   **Multi-User Architecture**: Secure, isolated workspaces for multiple users with Master Registry authentication.
*   **Automated Sync**: Instantly saves parsed data to user-specific Google Sheets and Drive folders.
*   **Batch Processing**: Drag-and-drop queue for processing multiple invoices sequentially.
*   **Anonymous Access**: fully supports anonymous (non-Google) users via custom login system.

## Requirements

*   Python 3.10+
*   Google Account (for Drive/Sheets integration)
*   `ngrok` (for exposing local API to Google Cloud)
*   Ollama (Local LLM) or OpenAI API Key

## Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/Project_APIR.git
cd Project_APIR
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

1.  **Environment Variables**: Create a `.env` file in the root directory:
    ```ini
    OPENAI_API_KEY=sk-...  # Optional if using Local LLM
    FLASK_ENV=development
    ```

2.  **Start Backend**:
    ```bash
    python app.py
    ```

3.  **Expose API**:
    In a separate terminal, start the tunnel:
    ```bash
    python start_tunnel.py
    ```

## Usage

### Google Apps Script Frontend (Recommended)
1.  Open the `Project_APIR_GAS` project in Google Script Editor.
2.  Update `CONFIG.FLASK_API_URL` with your **ngrok URL**.
3.  Deploy as "Web App" -> execute as **Me** -> access **Anyone**.
4.  Share the URL with users!

### CLI Mode
Process a folder of invoices without a UI:
```bash
python -m src.main --input "path/to/invoices"
```
