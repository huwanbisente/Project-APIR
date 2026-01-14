/**
 * ==========================================
 * 📡 RENDER KEEP-ALIVE SYSTEM
 * ==========================================
 * This script is dedicated to keeping the Render.com Free Tier instance alive.
 * It strictly calls the /health endpoint and DOES NOT incur LLM costs.
 */

/**
 * Pings the Render API to prevent cold-start spin down.
 * Run this every 10-15 minutes via Trigger.
 */
function keepAlive() {
  // Use the global CONFIG from Code.gs
  const url = CONFIG.FLASK_API_URL + "/health";
  try {
    const res = UrlFetchApp.fetch(url, { muteHttpExceptions: true });
    Logger.log("Keep-Alive Ping: " + res.getResponseCode());
  } catch (e) {
    Logger.log("Keep-Alive Failed: " + e.toString());
  }
}

/**
 * Setup Trigger helper
 * Run this function once manually to install the trigger.
 */
function setupKeepAliveTrigger() {
  // Delete existing triggers to prevent duplicates
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(t => {
    if (t.getHandlerFunction() === 'keepAlive') {
      ScriptApp.deleteTrigger(t);
    }
  });

  // Create new trigger (Every 10 minutes)
  ScriptApp.newTrigger('keepAlive')
    .timeBased()
    .everyMinutes(10) 
    .create();
    
  Logger.log("Keep-Alive trigger installed: Every 10 mins.");
}
