import pyautogui
import tkinter as tk
import os
from dotenv import load_dotenv
import time
import threading
import requests
import json
from PIL import Image, ImageFilter
import io

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Dictionary to track snapshots and their respective timestamps
screenshots = {}

def send_screenshot():
    timestamp = int(time.time())
    file_path = f"screenshot_{timestamp}.png"

    try:
        # Validate environment variables
        if not BOT_TOKEN or not CHAT_ID:
            print("ERROR: BOT_TOKEN or CHAT_ID not set in .env file")
            return None

        screenshot = pyautogui.screenshot()
        screenshot.save(file_path)

        # Store the snap info with timestamp for eventual cleanup
        screenshots[file_path] = timestamp

        # Blur the screenshot
        blurred = screenshot.filter(ImageFilter.BLUR)
        blurred_bytes = io.BytesIO()
        blurred.save(blurred_bytes, format='PNG')
        blurred_bytes.seek(0)

        # Create inline keyboard JSON with reveal button
        keyboard = {
            "inline_keyboard": [[{
                "text": "Scan & Earn",
                "callback_data": f"reveal_snap_{file_path}"
            }]]
        }
        reply_markup = json.dumps(keyboard)

        # Send blurred screenshot to telegram channel with button using direct API
        print(f"Sending screenshot to Telegram (Chat ID: {CHAT_ID})...")
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        
        files = {"photo": blurred_bytes}
        data = {
            "chat_id": CHAT_ID,
            "caption": "Blurred screenshot. Click the button to reveal.",
            "reply_markup": reply_markup
        }
        
        response = requests.post(url, files=files, data=data)
        
        if response.status_code == 200:
            print(f"✓ Screenshot sent successfully: {file_path}")
            return file_path
        else:
            error_msg = response.json().get("description", "Unknown error")
            print(f"✗ ERROR sending screenshot: {error_msg}")
            print(f"  Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"✗ ERROR sending screenshot: {e}")
        print(f"  BOT_TOKEN set: {bool(BOT_TOKEN)}")
        print(f"  CHAT_ID set: {bool(CHAT_ID)}")
        return None



def cleanup_screenshots():
    """Delete screenshots that are older than 20 minutes (1200 seconds)"""
    current_time = int(time.time())
    to_delete = []

    for file_path, timestamp in screenshots.items():
        if current_time - timestamp > 1200:  # timer has passed 20minutes
            try:
                os.remove(file_path)
                to_delete.append(file_path)
                print(f"Deleted old screenshot: {file_path}")
            except FileNotFoundError:
                # File was already deleted, just remove from tracking
                to_delete.append(file_path)
                print(f"Screenshot {file_path} was already deleted")
            except OSError as e:
                print(f"Error deleting {file_path}: {e}")

    # Remove from tracking dictionary
    for file_path in to_delete:
        del screenshots[file_path]

    # Schedule next cleanup in 60 seconds
    threading.Timer(60, cleanup_screenshots).start()

def on_button_click():
    print("\n--- Snap button clicked ---")
    send_screenshot()

def start_gui():
    # Validate environment at startup
    if not BOT_TOKEN:
        print("⚠ WARNING: BOT_TOKEN not found in .env file")
    if not CHAT_ID:
        print("⚠ WARNING: CHAT_ID not found in .env file")
    
    print("Starting screenshot GUI...")
    print(f"BOT_TOKEN: {'✓ Set' if BOT_TOKEN else '✗ Not set'}")
    print(f"CHAT_ID: {'✓ Set' if CHAT_ID else '✗ Not set'}")
    
    # Start the cleanup loop
    cleanup_screenshots()

    app = tk.Tk()
    app.title("Snap Sender")
    app.geometry("200x80")

    button = tk.Button(app, text="Snap!", command=on_button_click)
    button.pack(pady=20)

    app.mainloop()


if __name__ == '__main__':
    start_gui()
