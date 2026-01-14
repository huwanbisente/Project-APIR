// CONFIGURATION
const CONFIG = {
  // Drive Folder to save PDFs (Optional: Keep if you still want a backup in Drive)
  DRIVE_FOLDER_ID: '1Bngh6rT7jmCxR3rlSby57ruLJSJDULlG', 
  
  // Sheet to save data
  SHEET_ID: '1QDGXT7-_0xnY3T-uviMxUBaMRyI2J9RSuLR9XVTuHXU',
  SHEET_NAME: 'Invoices',
  
  // FLASK API CONFIGURATION
  // IMPORTANT: Replace this with your NGROK URL (e.g., https://abc-123.ngrok-free.app)
  FLASK_API_URL: 'REPLACE_WITH_YOUR_NGROK_URL' 
};

function doGet(e) {
  return HtmlService.createHtmlOutputFromFile('Index')
      .setTitle('Invoice AI Hub')
      .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

/**
 * Handles the file upload from client, sends to Flask API, and saves to Sheet.
 */
function processInvoiceUpload(base64Data, filename, mimeType) {
  try {
    // 1. (Optional) Save backup to Drive
    const folder = DriveApp.getFolderById(CONFIG.DRIVE_FOLDER_ID);
    const decoded = Utilities.base64Decode(base64Data);
    const blob = Utilities.newBlob(decoded, mimeType, filename);
    const file = folder.createFile(blob);
    const fileUrl = file.getUrl();
    
    // 2. Call Flask API
    const apiResult = callFlaskAPI(blob, filename);
    
    if (!apiResult.success) {
      throw new Error("API Error: " + apiResult.error);
    }
    
    const structuredData = apiResult.data;
    structuredData.file_url = fileUrl; // Add Drive URL to metadata

    // 3. Save to Sheet
    const saveResult = saveToSheet(structuredData);
    
    if (!saveResult.success) {
      throw new Error("Sheet Save Error: " + saveResult.error);
    }

    return {
      success: true,
      data: structuredData
    };

  } catch (error) {
    Logger.log("Error in processInvoiceUpload: " + error.toString());
    return {
      success: false,
      error: error.toString()
    };
  }
}

/**
 * Sends the file blob to the Flask API for processing
 */
function callFlaskAPI(blob, filename) {
  const url = CONFIG.FLASK_API_URL + "/api/parse";
  
  // Construct Multipart Form Data
  // UrlFetchApp automatically handles multipart if payload has blob
  const payload = {
    "file": blob
  };
  
  const options = {
    "method": "post",
    "payload": payload,
    "muteHttpExceptions": true
  };
  
  try {
    const response = UrlFetchApp.fetch(url, options);
    const responseCode = response.getResponseCode();
    const responseBody = response.getContentText();
    
    if (responseCode !== 200) {
      Logger.log("Flask API Failed: " + responseBody);
      return { success: false, error: "Flask API returned " + responseCode + ": " + responseBody };
    }
    
    const json = JSON.parse(responseBody);
    return json; // Expecting { success: true, data: {...} }
    
  } catch (e) {
    Logger.log("Fetch Error: " + e.toString());
    return { success: false, error: "Connection refused. Is Flask/Ngrok running? " + e.toString() };
  }
}

/**
 * Saves the extracted data to the Google Sheet
 */
function saveToSheet(data) {
  try {
    const ss = SpreadsheetApp.openById(CONFIG.SHEET_ID);
    let sheet = ss.getSheetByName(CONFIG.SHEET_NAME);
    
    // Create sheet if not exists
    if (!sheet) {
      sheet = ss.insertSheet(CONFIG.SHEET_NAME);
      // Add Headers
      sheet.appendRow([
        "Vendor", "Invoice #", "Date", "Due Date", "Tax", "Total", "Currency",
        "Item Description", "Qty", "Unit Price", "Amount", "File URL", "Timestamp"
      ]);
      // Style headers
      sheet.getRange(1, 1, 1, 13).setFontWeight("bold").setBackground("#e0e7ff");
    }

    const timestamp = new Date();
    // Handle potential null/undefined values safely
    const headers = [
      data.vendor_name || "",
      data.invoice_number || "",
      data.invoice_date || "",
      data.due_date || "",
      data.tax_amount || 0,
      data.total_amount || 0,
      data.currency || "USD"
    ];

    // Flatten line items
    if (data.line_items && data.line_items.length > 0) {
      data.line_items.forEach(item => {
        const row = [
          ...headers,
          item.description || "",
          item.quantity || 0,
          item.unit_price || 0,
          item.amount || 0,
          data.file_url,
          timestamp
        ];
        sheet.appendRow(row);
      });
    } else {
      // Save header only if no items
      const row = [
        ...headers,
        "", "", "", "",
        data.file_url,
        timestamp
      ];
      sheet.appendRow(row);
    }

    return { success: true };

  } catch (e) {
    Logger.log("Save Error: " + e.toString());
    return { success: false, error: e.toString() };
  }
}
