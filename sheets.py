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


# --- CONFIG (I1=last_run_date, J1=sana, K-N ustunlar: Account, Limit, Sent_Today, Total_Sent) ---


def get_config(sheet_name="LeadsBot"):
  client = get_sheets_client()
  sheet = client.open(sheet_name).worksheet("Config")
  rows = sheet.get_all_values()

  config = {"last_run_date": "", "accounts": {}}

  for idx, row in enumerate(rows):
    # I1 (9-ustun) va J1 (10-ustun) dan sanani o'qiymiz
    if idx == 0 and len(row) >= 10:
      if row[8].strip().lower() == "last_run_date":
        config["last_run_date"] = row[9].strip()

    # 2-qatordan boshlab akkauntlarni o'qiymiz (K=11, L=12, M=13, N=14 ustunlar)
    if idx >= 1 and len(row) >= 14:
      acc_name = row[10].strip().lower()  # K ustuni: Account nomi
      if acc_name and acc_name != "account":
        try:
          limit = int(row[11])  # L ustuni: Limit
        except:
          limit = 10
        try:
          sent_today = int(row[12])  # M ustuni: Sent_Today
        except:
          sent_today = 0
        try:
          total_sent = int(row[13])  # N ustuni: Total_Sent
        except:
          total_sent = 0

        config["accounts"][acc_name] = {
            "limit": limit,
            "sent_today": sent_today,
            "total_sent": total_sent,
        }
  return config


def update_account_stats(
    account_name, sent_today, total_sent, sheet_name="LeadsBot"
):
  client = get_sheets_client()
  sheet = client.open(sheet_name).worksheet("Config")
  cell = sheet.find(account_name, in_column=11)  # K ustunidan qidiradi (11-ustun)
  if cell:
    row = cell.row
    sheet.update_cell(row, 13, str(sent_today))  # M ustuni (Sent_Today)
    sheet.update_cell(row, 14, str(total_sent))  # N ustuni (Total_Sent)


def update_last_run_date(date_str, sheet_name="LeadsBot"):
  client = get_sheets_client()
  sheet = client.open(sheet_name).worksheet("Config")
  sheet.update_cell(1, 10, date_str)  # J1 katagiga sanani yozadi


def reset_daily_counts(sheet_name="LeadsBot"):
  client = get_sheets_client()
  sheet = client.open(sheet_name).worksheet("Config")
  rows = sheet.get_all_values()
  for idx, row in enumerate(rows):
    if idx >= 1 and len(row) >= 13:
      acc_name = row[10].strip().lower()
      if acc_name and acc_name != "account":
        sheet.update_cell(
            idx + 1, 13, "0"
        )  # M ustunini (Sent_Today) 0 ga tushiradi
