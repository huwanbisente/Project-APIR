// CONFIGURATION
const CONFIG = {
  // MASTER Root Folder for all User Data
  ROOT_FOLDER_ID: '1Bngh6rT7jmCxR3rlSby57ruLJSJDULlG', 
  
  // USER DATABASE SHEET ID
  // (The central registry for all users)
  USER_DB_ID: '1ZIWROdf4T7M5f-zFHa_HJjGlCSikWpPkBlNb7IwLU4o',
  
  // FLASK API CONFIGURATION
  FLASK_API_URL: 'https://project-apir.onrender.com', 
  API_ENDPOINT: '/api/parse'
};

function doGet(e) {
  return HtmlService.createHtmlOutputFromFile('Index')
      .setTitle('Invoice AI Hub')
      .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

// ==========================================
// 🧠 PUBLIC API (Called from Client)
// ==========================================

/**
 * Custom Login Function
 * Verifies Email/Password against Master User DB
 */
function login(email, password) {
  try {
    const isAuthenticated = MasterUserDB.verifyCredentials(email, password);
    if (!isAuthenticated) {
      return { success: false, error: "Invalid Email or Password" };
    }
    
    // Ensure resources exist (Folder/Sheet)
    const resources = UserResourceManager.get(email);
    
    // Check if we need to backfill links in the DB (for manually added users)
    MasterUserDB.updateLinksIfNeeded(email, resources.folderId, resources.sheetId);
    
    return { success: true, email: email };
  } catch (e) {
    return { success: false, error: e.toString() };
  }
}

/**
 * Gets the user's session data
 * REQUIRES email since we are in anonymous mode
 */
function getUserData(userEmail) {
  try {
    if (!userEmail) throw new Error("No email provided");
    
    const resources = UserResourceManager.get(userEmail);
    
    // Read history from sheet
    const ss = SpreadsheetApp.openById(resources.sheetId);
    const sheet = ss.getSheets()[0];
    const data = sheet.getDataRange().getValues();
    
    const history = [];
    if (data.length > 1) {
      for (let i = 1; i < data.length; i++) {
        const row = data[i];
        history.push({
           vendor_name: row[0],
           invoice_number: row[1],
           invoice_date: row[2] ? row[2].toString() : "",
           due_date: row[3] ? row[3].toString() : "",
           tax_amount: row[4],
           total_amount: row[5],
           currency: row[6],
           line_items: [{
              description: row[7],
              quantity: row[8],
              unit_price: row[9],
              amount: row[10]
           }],
           file_url: row[11],
           timestamp: row[12] ? row[12].toString() : ""
        });
      }
    }

    return {
      success: true,
      email: userEmail,
      history: history.reverse()
    };
  } catch (e) {
    return { success: false, error: e.toString() };
  }
}

/**
 * CLEARS all data for the user
 */
function clearUserWorkspace(userEmail) {
  try {
    if (!userEmail) throw new Error("No email provided");
    UserResourceManager.clear(userEmail);
    return { success: true };
  } catch(e) {
    return { success: false, error: e.toString() };
  }
}

/**
 * Handles file upload -> API -> User Sheet
 */
function processInvoiceUpload(base64Data, filename, mimeType, userEmail) {
  try {
    if (!userEmail) throw new Error("No email provided");
    
    const resources = UserResourceManager.get(userEmail);
    
    // 1. Save to User's Folder
    const folder = DriveApp.getFolderById(resources.folderId);
    const decoded = Utilities.base64Decode(base64Data);
    const blob = Utilities.newBlob(decoded, mimeType, filename);
    const file = folder.createFile(blob);
    const fileUrl = file.getUrl();
    
    // 2. Call Flask API
    const apiResult = callFlaskAPI(blob, filename);
    
    if (!apiResult.success) {
      throw new Error("API Error: " + apiResult.error);
    }
    
    const invoiceList = Array.isArray(apiResult.data) ? apiResult.data : [apiResult.data];
    let savedCount = 0;

    invoiceList.forEach(invoice => {
        invoice.file_url = fileUrl;
        
        // 3. Save to User's Sheet
        const saveResult = saveToUserSheet(resources.sheetId, invoice);
        if (saveResult.success) savedCount++;
    });

    return {
      success: true,
      data: invoiceList,
      message: `Processed ${savedCount} invoices.`
    };

  } catch (error) {
    Logger.log("Error: " + error.toString());
    return { success: false, error: error.toString() };
  }
}

// ==========================================
// 🛠️ INTERNAL TOOLS
// ==========================================

const UserResourceManager = {
  get: function(email) {
    // 1. Normalize Email (Crucial for isolation)
    email = email.trim().toLowerCase();
    
    // 2. CHECK REGISTRY FOR EXISTING LINKS FIRST (Best for Persistence)
    const storedLinks = MasterUserDB.getLinks(email);
    if (storedLinks) {
       try {
         // Verify they still exist
         const folder = DriveApp.getFolderById(storedLinks.folderId);
         const sheet = SpreadsheetApp.openById(storedLinks.sheetId);
         return { folderId: storedLinks.folderId, sheetId: storedLinks.sheetId };
       } catch(e) {
         // If links are broken/deleted, proceed to create new
         Logger.log("Stored links invalid, recreating workspace...");
       }
    }
    
    // 3. Resolve/Create directly from Drive (Fallback)
    const root = DriveApp.getFolderById(CONFIG.ROOT_FOLDER_ID);
    const folderName = `APIR_Workspace_${email}`;
    const sheetName = `APIR_Data_${email}`;
    
    const folders = root.getFoldersByName(folderName);
    let folder, sheet;
    
    if (folders.hasNext()) {
      folder = folders.next();
      const files = folder.getFilesByName(sheetName);
      if (files.hasNext()) {
        sheet = SpreadsheetApp.open(files.next());
      } else {
        sheet = this.createSheet(folder, sheetName);
      }
    } else {
      folder = root.createFolder(folderName);
      sheet = this.createSheet(folder, sheetName);
    }
    
    const resources = { folderId: folder.getId(), sheetId: sheet.getId() };
    return resources;
  },
  
  createSheet: function(folder, name) {
    const ss = SpreadsheetApp.create(name);
    const file = DriveApp.getFileById(ss.getId());
    file.moveTo(folder); 
    
    const sheet = ss.getSheets()[0];
    sheet.setName("Invoices");
    sheet.appendRow([
        "Vendor", "Invoice #", "Date", "Due Date", "Tax", "Total", "Currency",
        "Item Description", "Qty", "Unit Price", "Amount", "File URL", "Timestamp"
    ]);
    sheet.getRange(1, 1, 1, 13).setFontWeight("bold").setBackground("#e0e7ff");
    return ss;
  },
  
  clear: function(email) {
    email = email.trim().toLowerCase();
    
    // 1. Get Folder ID from Registry (Most reliable method)
    const storedLinks = MasterUserDB.getLinks(email);
    if (storedLinks && storedLinks.folderId) {
       try {
         DriveApp.getFolderById(storedLinks.folderId).setTrashed(true);
       } catch(e) {
         Logger.log("Could not trash folder by ID: " + e.toString());
       }
    }

    // 2. Fallback: Search by Name (For legacy/duplicate folders)
    const root = DriveApp.getFolderById(CONFIG.ROOT_FOLDER_ID);
    const folderName = `APIR_Workspace_${email}`;
    const folders = root.getFoldersByName(folderName);
    while (folders.hasNext()) {
      folders.next().setTrashed(true);
    }
    
    // 3. Clear Links from Master Registry
    MasterUserDB.clearLinks(email);
  }
};

const MasterUserDB = {
  getLinks: function(email) {
    const ss = SpreadsheetApp.openById(CONFIG.USER_DB_ID);
    const sheet = ss.getSheets()[0];
    const data = sheet.getDataRange().getValues();
    
    for (let i = 1; i < data.length; i++) {
        // Soft match email (case insensitive search against DB)
        if (data[i][0].toString().toLowerCase() === email) {
            const folderUrl = data[i][1];
            const sheetUrl = data[i][2];
            
            if (folderUrl && sheetUrl) {
                try {
                   // Extract IDs from URLs
                   const folderId = folderUrl.match(/[-\w]{25,}/)[0];
                   const sheetId = sheetUrl.match(/[-\w]{25,}/)[0];
                   return { folderId: folderId, sheetId: sheetId };
                } catch(e) {
                   return null; 
                }
            }
        }
    }
    return null;
  },

  verifyCredentials: function(email, password) {
    const ss = SpreadsheetApp.openById(CONFIG.USER_DB_ID);
    const sheet = ss.getSheets()[0];
    const data = sheet.getDataRange().getValues();
    
    // Normalize input
    email = email.trim().toLowerCase();

    // Skip Header (Row 0)
    for (let i = 1; i < data.length; i++) {
        // Compare lowercased DB email vs lowercased input
        if (data[i][0].toString().toLowerCase() == email && data[i][4] == password) {
            return true;
        }
    }
    return false;
  },

  updateLinksIfNeeded: function(email, folderId, sheetId) {
    const ss = SpreadsheetApp.openById(CONFIG.USER_DB_ID);
    const sheet = ss.getSheets()[0];
    const data = sheet.getDataRange().getValues();
    
    email = email.trim().toLowerCase();

    for (let i = 1; i < data.length; i++) {
        if (data[i][0].toString().toLowerCase() == email) {
            // Check if links are empty (Col B and C -> Index 1 and 2)
            if (!data[i][1] || !data[i][2]) {
                const folderUrl = DriveApp.getFolderById(folderId).getUrl();
                const sheetUrl = DriveApp.getFileById(sheetId).getUrl();
                
                // Update Row (1-based index = i+1)
                sheet.getRange(i + 1, 2).setValue(folderUrl);
                sheet.getRange(i + 1, 3).setValue(sheetUrl);
                sheet.getRange(i + 1, 4).setValue(new Date()); 
            }
            break;
        }
    }
  },

  clearLinks: function(email) {
    const ss = SpreadsheetApp.openById(CONFIG.USER_DB_ID);
    const sheet = ss.getSheets()[0];
    const data = sheet.getDataRange().getValues();
    
    email = email.trim().toLowerCase();

    for (let i = 1; i < data.length; i++) {
        if (data[i][0].toString().toLowerCase() == email) {
             // Clear Col B (2), C (3), D (4Joined)
             // Row is i+1
             sheet.getRange(i+1, 2, 1, 3).clearContent();
             break;
        }
    }
  }
};

function callFlaskAPI(blob, filename) {
  const url = CONFIG.FLASK_API_URL + "/api/parse";
  const payload = { "file": blob };
  const options = { "method": "post", "payload": payload, "muteHttpExceptions": true };
  
  try {
    const response = UrlFetchApp.fetch(url, options);
    if (response.getResponseCode() !== 200) {
      return { success: false, error: response.getContentText() };
    }
    return JSON.parse(response.getContentText());
  } catch (e) {
    return { success: false, error: "Connection error: " + e.toString() };
  }
}

function saveToUserSheet(sheetId, data) {
  try {
    const ss = SpreadsheetApp.openById(sheetId);
    const sheet = ss.getSheets()[0];
    const timestamp = new Date();
    
    const common = [
      data.vendor_name || "",
      data.invoice_number || "",
      data.invoice_date || "",
      data.due_date || "",
      data.tax_amount || 0,
      data.total_amount || 0,
      data.currency || "USD"
    ];

    if (data.line_items && data.line_items.length > 0) {
      data.line_items.forEach(item => {
        sheet.appendRow([...common, item.description||"", item.quantity||0, item.unit_price||0, item.amount||0, data.file_url, timestamp]);
      });
    } else {
      sheet.appendRow([...common, "", "", "", "", data.file_url, timestamp]);
    }
    return { success: true };
  } catch (e) {
    return { success: false, error: e.toString() };
  }
}
