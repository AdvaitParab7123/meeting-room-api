import ssl
import sys
import gspread
from google.oauth2.service_account import Credentials
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict
import uvicorn

# Ensure SSL module is available
if "ssl" not in sys.modules:
    raise ImportError("SSL module is not available. Try using a different Python environment.")

app = FastAPI()
security = HTTPBasic()

# Hardcoded user credentials (For production, use a proper authentication mechanism)
USERNAME = "admin"
PASSWORD = "password123"

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != USERNAME or credentials.password != PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return credentials

# Load Google Sheets credentials
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("service_account.json", scopes=scope)
client = gspread.authorize(creds)

# Open Google Sheet
SHEET_NAME = "Meeting Room Bookings"
try:
    sheet = client.open(SHEET_NAME).sheet1
except Exception as e:
    raise Exception(f"Failed to open Google Sheet: {e}")

# Data storage
meeting_rooms = {}  # Dictionary to store room details
bookings = []  # List to store bookings

class Room(BaseModel):
    name: str
    capacity: int
    amenities: List[str]

class Booking(BaseModel):
    room_name: str
    start_time: datetime
    end_time: datetime
    booked_by: str

@app.post("/add_room")
def add_room(room: Room, credentials: HTTPBasicCredentials = Depends(authenticate)):
    if room.name in meeting_rooms:
        raise HTTPException(status_code=400, detail="Room already exists")
    meeting_rooms[room.name] = room.dict()
    return {"message": "Room added successfully"}

@app.get("/rooms")
def list_rooms(credentials: HTTPBasicCredentials = Depends(authenticate)):
    return meeting_rooms

@app.post("/book_room")
def book_room(booking: Booking, credentials: HTTPBasicCredentials = Depends(authenticate)):
    if booking.room_name not in meeting_rooms:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Check for conflicts
    for b in bookings:
        if b["room_name"] == booking.room_name and not (
            booking.end_time <= b["start_time"] or booking.start_time >= b["end_time"]
        ):
            raise HTTPException(status_code=400, detail="Room already booked for this time")
    
    # Save to local bookings
    booking_data = booking.dict()
    bookings.append(booking_data)

    # Save to Google Sheets
    try:
        sheet.append_row([
            booking.room_name,
            booking.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            booking.end_time.strftime("%Y-%m-%d %H:%M:%S"),
            booking.booked_by
        ])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save booking to Google Sheets: {e}")

    return {"message": "Room booked successfully"}

@app.get("/bookings")
def list_bookings(credentials: HTTPBasicCredentials = Depends(authenticate)):
    return bookings

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
