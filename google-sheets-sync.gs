/**
 * Auto-syncs the garden leaderboard into this Google Sheet.
 *
 * SETUP
 * 1. Open (or create) a Google Sheet.
 * 2. Extensions -> Apps Script.
 * 3. Delete the placeholder code, paste this whole file in, and save.
 * 4. Set FIREBASE_PROJECT_ID below to match your firebase-config.js
 *    (the "projectId" value).
 * 5. Run the "syncLeaderboard" function once from the toolbar (▶ button).
 *    The first run will ask you to authorize it — that's normal,
 *    it's just Google asking permission for the script to edit
 *    this sheet.
 * 6. To keep it updating automatically, run "setupTrigger" once too.
 *    This adds a time-based trigger that refreshes the sheet every
 *    15 minutes. (Change the interval in setupTrigger() if you want.)
 *
 * This works without any Firebase credentials because the site's
 * Firestore security rules allow public read access to the "scans"
 * collection (same access the public leaderboard page already uses).
 */

const FIREBASE_PROJECT_ID = "PASTE_YOUR_FIREBASE_PROJECT_ID_HERE";
const SHEET_NAME = "Leaderboard";

function syncLeaderboard() {
  const url = "https://firestore.googleapis.com/v1/projects/" + FIREBASE_PROJECT_ID +
    "/databases/(default)/documents/scans?pageSize=300";

  const response = UrlFetchApp.fetch(url, { muteHttpExceptions: true });
  if (response.getResponseCode() !== 200) {
    throw new Error("Firestore request failed: " + response.getContentText());
  }
  const data = JSON.parse(response.getContentText());

  const rows = (data.documents || []).map(function (doc) {
    const fields = doc.fields || {};
    const name = fields.name && fields.name.stringValue ? fields.name.stringValue : "";
    const countField = fields.count || {};
    const count = parseInt(countField.integerValue || countField.doubleValue || 0, 10);
    const updatedAt = fields.updatedAt && fields.updatedAt.timestampValue
      ? fields.updatedAt.timestampValue : "";
    return [name, count, updatedAt];
  });

  rows.sort(function (a, b) { return b[1] - a[1]; });

  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) sheet = ss.insertSheet(SHEET_NAME);
  sheet.clear();

  sheet.appendRow(["Name", "Plants Found", "Last Scan (UTC)"]);
  sheet.getRange(1, 1, 1, 3).setFontWeight("bold");

  if (rows.length > 0) {
    sheet.getRange(2, 1, rows.length, 3).setValues(rows);
  }

  sheet.autoResizeColumns(1, 3);
}

function setupTrigger() {
  // remove any existing triggers for this function first, so re-running
  // this doesn't create duplicates
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === "syncLeaderboard") {
      ScriptApp.deleteTrigger(t);
    }
  });
  ScriptApp.newTrigger("syncLeaderboard")
    .timeBased()
    .everyMinutes(15)
    .create();
}
