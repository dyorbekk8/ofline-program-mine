import os
import json
import time
import random
import gspread
from google.oauth2.service_account import Credentials

# Scope va Ruxsatlar
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Railway Environment Variable'dan JSON ni o'qish
json_creds_str = os.getenv('SERVICE_ACCOUNT_JSON')

if json_creds_str:
    creds_dict = json.loads(json_creds_str)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
else:
    # Lokal kompyuterda ishlatish uchun
    creds = Credentials.from_service_account_file('service_account.json', scopes=SCOPES)

client = gspread.authorize(creds)

# Google Sheets jadvalingiz aniq nomi
SHEET_NAME = "Cold Email Leads"

def main():
    print("Bot 24/7 ishga tushdi va Google Sheets'ga ulandi...")
    sheet = client.open(SHEET_NAME).sheet1
    
    while True:
        try:
            records = sheet.get_all_records()
            print(f"Jami leadlar soni: {len(records)}")
            
            # Bu yerda leadlarni birma-bir ko'rib chiqish va xabar yuborish mantiqi bo'ladi
            
        except Exception as e:
            print(f"Xatolik yuz berdi: {e}")
            
        # Har 5 daqiqada tekshirib turish
        time.sleep(300)

if __name__ == "__main__":
    main()
