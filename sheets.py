from datetime import datetime
import json
import os
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_sheets_client():
  creds_json = os.getenv("GOOGLE_CREDS_JSON")
  if creds_json:
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
  else:
    creds = Credentials.from_service_account_file(
        "service_account.json", scopes=SCOPES
    )
  return gspread.authorize(creds)


def get_pending_leads(sheet_name="LeadsBot"):
  client = get_sheets_client()
  sheet = client.open(sheet_name).worksheet("Leads")
  records = sheet.get_all_records()

  pending_leads = []
  for idx, row in enumerate(records, start=2):
    if str(row.get("Status")).strip().lower() == "pending":
      row["row_index"] = idx
      pending_leads.append(row)

  return pending_leads


def update_lead_status(
    row_index, status="Sent", template_id=1, sheet_name="LeadsBot"
):
  client = get_sheets_client()
  sheet = client.open(sheet_name).worksheet("Leads")
  current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

  sheet.update_cell(row_index, 6, status)  # F ustuni (Status)
  sheet.update_cell(row_index, 7, template_id)  # G ustuni (Template_ID)
  sheet.update_cell(row_index, 8, current_time)  # H ustuni (Date_Sent)


# --- CONFIG (K va L ustunlari) ---


def get_config(sheet_name="LeadsBot"):
  client = get_sheets_client()
  sheet = client.open(sheet_name).worksheet("Config")
  rows = sheet.get_all_values()
  config = {}
  for row in rows:
    if len(row) >= 12:
      k = row[10].strip()  # K ustuni (11-chi)
      v = row[11].strip()  # L ustuni (12-chi)
      if k:
        config[k] = v
  return config


def update_config(key, value, sheet_name="LeadsBot"):
  client = get_sheets_client()
  sheet = client.open(sheet_name).worksheet("Config")
  try:
    cell = sheet.find(key, in_column=11)
    if cell:
      sheet.update_cell(cell.row, 12, str(value))
  except Exception:
    col_k = sheet.col_values(11)
    next_row = len(col_k) + 1
    sheet.update_cell(next_row, 11, key)
    sheet.update_cell(next_row, 12, str(value))
