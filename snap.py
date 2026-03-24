import pyautogui
import requests
import tkinter as tk
import os
from dotenv import load_dotenv
import time
import threading

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Dictionary to track snapshots and their respective timestamps
screenshots = {}

def send_screenshot():
    timestamp = int(time.time())
    file_path = f"screenshot_{timestamp}.png"

    screenshot = pyautogui.screenshot()
    screenshot.save(file_path)

    # Store the snap info with timestamp for eventual cleanup
    screenshots[file_path] = timestamp

    # Send copy of snap to telegram channel
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    with open(file_path, "rb") as photo:
        requests.post(url, data={"chat_id": CHAT_ID}, files={"photo": photo})

    # delete snaps that are older than 20 minutes
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
            except OSError as e:
                print(f"Error deleting {file_path}: {e}")

    # Remove snap from tracking dictionary
    for file_path in to_delete:
        del screenshots[file_path]

    # Schedule next cleanup in 1 minute
    threading.Timer(60, cleanup_screenshots).start()

def on_button_click():
    send_screenshot()

# Start the cleanup loop
cleanup_screenshots()

app = tk.Tk()
app.title("Snap Sender")

button = tk.Button(app, text="Snap!", command=on_button_click)
button.pack(pady=20)

app.mainloop()
