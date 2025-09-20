# python -m ui.other_scripts.do_something.py

import time
import random
import pygetwindow as gw
import subprocess
from pynput.keyboard import Controller as KeyboardController, Key
from pynput.mouse import Controller as MouseController, Button

# Initialize controllers for real keyboard & mouse
keyboard = KeyboardController()
mouse = MouseController()

# Work-related applications
work_apps = {
    "VSCode": "C:\\Program Files\\Microsoft VS Code\\Code.exe",
    "Chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "Notepad": "C:\\Windows\\System32\\notepad.exe",
    # "GitBash": "C:\\Program Files\\Git\\git-bash.exe",
    # "Outlook": "C:\\Program Files\\Microsoft Office\\root\\Office16\\OUTLOOK.EXE"
}

# FAQs to type
faq_list = [
    "What is AWS Lambda?",
    "How does EC2 scaling work?",
    "What are Python decorators?",
    "How to use SQL joins?",
    "What is an S3 bucket?",
    "How to optimize SQL queries?",
    "What is AWS IAM?",
    "How to handle exceptions in Python?",
    "Difference between UNION and UNION ALL?",
    "What is AWS VPC?",
]

def open_and_close_work_app():
    """Opens a random work-related application, waits, and then closes it."""
    app_name, app_path = random.choice(list(work_apps.items()))  # Select a random application
    print(f"Opening application: {app_name}")
    process = subprocess.Popen(app_path, shell=True)
    time.sleep(random.randint(5, 10))  # Wait inside the app
    process.terminate()  # Close the application
    print(f"Closed application: {app_name}")

def move_mouse_and_click():
    """Moves the mouse cursor randomly and performs a real click."""
    x, y = random.randint(300, 1200), random.randint(200, 800)  # Center screen region
    mouse.position = (x, y)
    time.sleep(random.uniform(0.5, 1.5))  # Smooth movement delay
    mouse.click(Button.left, 1)  # Perform a real left mouse click
    print(f"Mouse moved to {x}, {y} and clicked")

def type_text_with_keyboard():
    """Simulates real keyboard typing using hardware-level keystrokes."""
    active_window = gw.getActiveWindowTitle()
    
    if active_window:
        print(f"Currently active window: {active_window}")

        if "Notepad" in active_window:
            print("Detected Notepad - Typing a random FAQ")
            faq = random.choice(faq_list)
            for char in faq:
                keyboard.press(char)  # Simulate real typing
                keyboard.release(char)
                time.sleep(random.uniform(0.05, 0.2))  # Add human-like delay
            keyboard.press(Key.enter)
            keyboard.release(Key.enter)
            move_mouse_and_click()  # Click after typing

        else:
            print("Typing a random FAQ in a generic window")
            faq = random.choice(faq_list)
            for char in faq:
                keyboard.press(char)
                keyboard.release(char)
                time.sleep(random.uniform(0.05, 0.2))  # Simulate natural typing
            keyboard.press(Key.enter)
            keyboard.release(Key.enter)

def switch_window():
    """Switches between open work-related applications."""
    windows = gw.getWindowsWithTitle("")
    if windows:
        random.choice(windows).activate()
        print("Switched to a random application window.")

def keep_system_active():
    """Runs continuously to keep the system active and tracked by HCL Nippon."""
    while True:
        open_and_close_work_app()  # Open & close an app
        for _ in range(5):  # Perform actions in a loop
            move_mouse_and_click()
            type_text_with_keyboard()
            switch_window()
            sleep_time = random.randint(10, 30)  # Random time between 10-30 seconds
            print(f"Waiting {sleep_time} seconds before next action...")
            time.sleep(sleep_time)

try:
    keep_system_active()
except KeyboardInterrupt:
    print("\nScript stopped by user.")
