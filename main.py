import os
import json
import uvicorn
import gspread
from fastapi import FastAPI
from google.oauth2.service_account import Credentials

app = FastAPI()

# Load Google service account credentials from Railway Shared Variable
service_account_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")

if service_account_json:
    credentials_info = json.loads(service_account_json)
    credentials = Credentials.from_service_account_info(credentials_info, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    gc = gspread.authorize(credentials)
else:
    raise ValueError("GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable not set")

@app.get("/")
def read_root():
    return {"message": "Meeting Room API is running!"}

# Example endpoint to read Google Sheet data
@app.get("/sheet/{sheet_id}/{worksheet_name}")
def read_sheet(sheet_id: str, worksheet_name: str):
    try:
        sheet = gc.open_by_key(sheet_id)
        worksheet = sheet.worksheet(worksheet_name)
        data = worksheet.get_all_records()
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
