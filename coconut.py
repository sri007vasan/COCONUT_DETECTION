import cv2
import numpy as np
import os
import time
import datetime
import pickle
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

FOLDER_PATH = r"C:\Users\ADMIN\Pictures\mavic2pro"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "1S1BNXFDYBy2Xk8X9288KQm96n7uV1bWh6dW0WZuoESQ"
SHEET_NAME = "sheet1"

def get_sheets_service():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                print("❌ Missing 'credentials.json'. Please download it from Google Cloud Console.")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    print("✅ Google Sheets API authentication successful!")
    return build("sheets", "v4", credentials=creds)

service = get_sheets_service()
if service:
    sheet = service.spreadsheets()
else:
    sheet = None

def classify_ball(image_path):
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Failed to load image: {image_path}")
        return

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    lower_green = np.array([35, 40, 40])
    upper_green = np.array([85, 255, 255])

    lower_yellow = np.array([20, 100, 100])
    upper_yellow = np.array([30, 255, 255])

    mask_green = cv2.inRange(hsv, lower_green, upper_green)
    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)

    green_pixels = cv2.countNonZero(mask_green)
    yellow_pixels = cv2.countNonZero(mask_yellow)
    
    if yellow_pixels > green_pixels:
        result = "MATURED!!-Ready to Cultivate"
    elif green_pixels > yellow_pixels:
        result = "IMMATURE-Wait to Cultivate"
    else:
        result = "No Clear Ball Detected"
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if sheet:
        log_to_google_sheets(image_path, result, timestamp)
    else:
        print("❌ Google Sheets API is not initialized. Skipping logging.")
    
    print(f"✅ [RESULT] {result} ({image_path}) at {timestamp}")

def log_to_google_sheets(image_name, result, timestamp):
    values = [[image_name, result, timestamp]]
    body = {"values": values}

    try:
        sheet.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A:C",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body,
        ).execute()
        print(f"✅ Logged to Google Sheets: {image_name} → {result} at {timestamp}")
    except Exception as e:
        print(f"❌ Failed to log to Google Sheets: {e}")

class ImageHandler(FileSystemEventHandler):
    """Watches the folder and processes new images."""
    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.lower().endswith((".png", ".jpg", ".jpeg")):
            time.sleep(1)
            
            print(f"📸 New image detected: {event.src_path}")
            classify_ball(event.src_path)

if os.path.exists(FOLDER_PATH):
    observer = Observer()
    event_handler = ImageHandler()
    observer.schedule(event_handler, FOLDER_PATH, recursive=False)
    observer.start()

    print(f"📂 Monitoring folder: {FOLDER_PATH}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
else:
    print(f"❌ Folder does not exist: {FOLDER_PATH}")
