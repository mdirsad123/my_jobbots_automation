"""
python -m python_code_practice.search_chatgpt_screenshot_problem
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path
import os
import pyautogui
import sys
import mss
import mss.tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from my_jobbots_automation.utils.debbuger_port_driver import get_driver # type: ignore

output_cache_file = Path(__file__).resolve().parent.parent / "output" / "cached_post.py"
output_cache_file.parent.mkdir(parents=True, exist_ok=True)

def search_prompt() -> str:
    return (
        f"""I have attached a screenshot of a programming problem. Please carefully read the problem from the image and solve it using Python. Requirements: - Provide a clean and correct Python solution - Briefly explain the core logic (no unnecessary explanation) - If the problem is algorithmic, mention time complexity - Assume this is an interview-style question"""
    )


def take_screenshot():
    filename = "screen1.png"

    with mss.mss() as sct:
        monitor = sct.monitors[1]
        sct_img = sct.grab(monitor)

        mss.tools.to_png(
            sct_img.rgb,
            sct_img.size,
            output=filename
        )

    # ✅ return FULL absolute path
    return os.path.abspath(filename)

def upload_screenshot(wait, screenshot_path: str):
    try:
        plus_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@id='composer-plus-btn']"))
        )
        plus_btn.click()
        time.sleep(2)
        add_files_btn = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//div[contains(text(),'Add photos') or contains(text(),'Add files')]")
            )
        )
        add_files_btn.click()

        time.sleep(2)
        pyautogui.write(screenshot_path)
        time.sleep(1)
        pyautogui.press('enter')
        print("Screenshot uploaded")
        time.sleep(2)
    except Exception as e:
        print(f"Screenshot upload failed: {e}")

def _try_upload_screenshot(wait, screenshot_path: str):
    try:
        file_input = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[@type='file']")
            )
        )

        file_input.send_keys(screenshot_path)
        print("Screenshot uploaded successfully")

    except Exception as e:
        print(f"Screenshot upload failed: {e}")

def ask_question_to_chatgpt():
    driver = get_driver()
    wait = WebDriverWait(driver, 30)

    driver.get("https://chatgpt.com/")
    time.sleep(5)

    prompt = search_prompt()
    screenshot_path = take_screenshot()

    # 3️⃣ Upload screenshot
    _try_upload_screenshot(wait, screenshot_path)

    # 1️⃣ Focus input box (contenteditable)
    input_box = wait.until(
        EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true']"))
    )
    input_box.click()
    time.sleep(1)

    # 2️⃣ Type FULL prompt (NO ENTER)
    input_box.send_keys(prompt)
    time.sleep(2)

    # 5️⃣ ONLY NOW click send
    send_btn = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[@id='composer-submit-button']"))
    )
    send_btn.click()

    print("✅ Prompt + Screenshot sent together")

# ✅ Allow command-line run
if __name__ == "__main__":
    msg = ask_question_to_chatgpt()
    print(msg)
