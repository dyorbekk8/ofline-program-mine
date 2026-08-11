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

  sheet.update_cell(row_index, 5, status)
  sheet.update_cell(row_index, 6, template_id)
  sheet.update_cell(row_index, 7, current_time)


# --- CONFIG (Kunlik limitlar uchun) ---


def get_config(sheet_name="LeadsBot"):
  client = get_sheets_client()
  sheet = client.open(sheet_name).worksheet("Config")
  data = sheet.get_all_records()
  return {row["Key"]: row["Value"] for row in data}


def update_config(key, value, sheet_name="LeadsBot"):
  client = get_sheets_client()
  sheet = client.open(sheet_name).worksheet("Config")
  cell = sheet.find(key)
  sheet.update_cell(cell.row, 2, value)  # B ustuni (Value)
