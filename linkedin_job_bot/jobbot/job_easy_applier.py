"""
python linkedin_job_bot/jobbot/job_easy_applier.py
python -m linkedin_job_bot.jobbot.job_easy_applier
"""

import time
import random
import pyautogui
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from utils.debbuger_port_driver import get_driver

def ensure_english_language(driver, wait):
    current_lang = driver.find_element(By.TAG_NAME, "html") \
                         .get_attribute("lang") or ""
    if current_lang.lower().startswith("en"):
        print(f"Already in English (lang={current_lang})")
        return

    print("Switching to English via settings…")
    orig_tab = driver.current_window_handle

    # — open a true new tab and navigate there —
    new_tab = driver.switch_to.new_window('tab')              # <–– Selenium v4 API
    print("Opened new tab, navigating to language settings")
    driver.get("https://www.linkedin.com/mypreferences/d/settings/language")

    # wait for the settings page
    wait.until(lambda d: "/settings/language" in d.current_url)

    # locate the dropdown (tag/name might differ slightly; adjust as needed)
    select = wait.until(EC.presence_of_element_located((By.TAG_NAME, "select")))
    for option in select.find_elements(By.TAG_NAME, "option"):
        if "English" in option.text:
            option.click()
            print("Selected English")
            break

    # Save if needed
    try:
        save = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(., 'Save')]")))
        save.click()
        print("Clicked Save")
    except TimeoutException:
        print("No Save button—assuming autosave")

    # wait for the main page to switch lang
    wait.until(lambda d: d.find_element(By.TAG_NAME, "html")
               .get_attribute("lang").lower().startswith("en"))

    # close settings tab, return to original
    driver.close()
    driver.switch_to.window(orig_tab)
    print("Back on original tab with English UI")
    driver.refresh()
    print("Original tab refreshed to pick up English UI")

    # (optional) wait until the Easy Apply button is visible again
    wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, ".jobs-apply-button--top-card button")))


def easy_apply_to_job(driver, job_url: str, resume_path: str) -> str:
    wait = WebDriverWait(driver, 15)
    driver.get(job_url)
    time.sleep(2)

    print("Ensuring English language...")
    ensure_english_language(driver, wait)

    if is_application_blocked(driver):
        return "application not acceptable"

    if not click_easy_apply(driver, wait):
        return "already applied"

    time.sleep(0.5)

    while True:
        time.sleep(0.5)

        upload_resume(wait, resume_path)
        auto_answer_fields(driver)
        select_yes_radios(driver, wait)

        if click_next_continue_review(driver):
            continue

        return submit_application(driver, wait)


def is_application_blocked(driver) -> bool:
    try:
        feedback_msg = driver.find_element(By.XPATH, "//span[@class='artdeco-inline-feedback__message']")
        if feedback_msg.is_displayed():
            print("Application is no longer acceptable: " + feedback_msg.text.strip())
            return True
    except:
        print("No blocking feedback message found.")
    return False


def click_easy_apply(driver, wait) -> bool:
    selectors = [
        (By.CSS_SELECTOR, ".jobs-apply-button--top-card button"),
        (By.CSS_SELECTOR, 'button[data-control-name="jobdetails_tqAopcard_inapply"]'),
        (By.XPATH, "//button[contains(., 'Easy Apply')]")
    ]
    for selector in selectors:
        try:
            btn = wait.until(EC.element_to_be_clickable(selector))
            btn.click()
            print(f"Clicked Easy Apply via {selector}")
            return True
        except TimeoutException:
            continue
    print("Easy Apply button not found.")
    return False


def upload_resume(wait, resume_path: str):
    try:
        selector = (By.CSS_SELECTOR, "label.jobs-document-upload__upload-button")
        upload_btn = wait.until(EC.element_to_be_clickable(selector))
        upload_btn.click()
        time.sleep(2)
        pyautogui.write(resume_path)
        time.sleep(1)
        pyautogui.press('enter')
        print("Resume uploaded")
        time.sleep(2)
    except Exception as e:
        print(f"Resume upload failed: {e}")


def auto_answer_fields(driver):
    for sel in driver.find_elements(By.TAG_NAME, "select"):
        opts = sel.find_elements(By.TAG_NAME, "option")
        if len(opts) > 1:
            opts[1].click()
            print("Selected second option from dropdown")

    inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='number']")
    for inp in inputs:
        if inp.get_attribute("value").strip():
            continue
        try:
            label = driver.find_element(By.XPATH, f"//label[@for='{inp.get_attribute('id')}']")
            label_text = label.text.strip().lower()
            if "notice period" in label_text:
                inp.send_keys("30")
                print("Set Notice Period: 30 days")
            else:
                val = random.randint(2, 3)
                inp.send_keys(str(val))
                print(f"Filled input with value: {val}")
        except Exception as e:
            print(f"Could not find label for input: {e}")


def select_yes_radios(driver, wait):
    for r in driver.find_elements(By.CSS_SELECTOR, "input[type='radio'][value='Yes']"):
        if not r.is_enabled():
            continue
        try:
            rid = r.get_attribute("id")
            lbl = driver.find_element(By.CSS_SELECTOR, f"label[for='{rid}']")
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"label[for='{rid}']"))).click()
            print(f"Selected 'Yes' for {rid}")
        except:
            r.click()
            print(f"Fallback click on 'Yes' for {r.get_attribute('id')}")


def click_next_continue_review(driver) -> bool:
    for btn in driver.find_elements(By.CSS_SELECTOR, "button.artdeco-button--primary.artdeco-button--2"):
        txt = btn.text.strip().lower()
        if txt in ("next", "review", "continue"):
            btn.click()
            print(f"Clicked '{txt.title()}'")
            time.sleep(2)
            return True
    return False


def submit_application(driver, wait) -> str:
    try:
        submit_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Submit application') or contains(., 'Submit')]"))
        )
        submit_btn.click()
        print("Application submitted successfully")
        return "submitted"
    except TimeoutException:
        print("Submit button not found")
        return "submit failed"

if __name__ == "__main__":
    driver = get_driver()
    job_url = "https://www.linkedin.com/jobs/view/4255688428/?alternateChannel=search&eBP=CwEAAAGXytSuP3sxrpLyXpoM4ZQF9vNom1PajUXzTEDt90NtyA3SCx2Z1xBhPZwkTb-skU3aaM0l8MSUOUlWY2GuaFwSVb0CEjDFEgtcR8uw7GNt9AmplQKxKjsopD51u7ZhWr8a_53L1D8kf9f2sdCKM1MNMVDzfccVq5qcsgPy0RT4Y1IlaoVbgAunBSFQL2l4iGkitd8q_NKsoe6UpFEVot6MmyMp1tMZXHGebF1zsufOzPTio7ENcAZBNRfVRuuzkeBrAn2JWSpd5wlYdlDrv0DlAYTp5JNngjH1ABSE8WXc9FUQSkEg1o12_Ls3XGIEqRvHFCzxVBIKjJXTY2oPZ-1IrNP3oiVNH-kMXb7BdmoVrOOjnq4PJua5Kn6kSwnEJ5e4TIfdc_ISt7d4bLyfEzNjW3EDQezWExizmzMTtCBmTztjOj7bbV18AN3fyiMs3pg&refId=MExyM5WheMqYNDgcPOP5CA%3D%3D&trackingId=vUgTK4mXxVRvVBRFphF6ig%3D%3D"
    output_file = r"C:\Users\erirs\projects\ird-projects\my_pyautomation\linkedin_job_bot\input\Md_Irshad__SSE_ind.pdf"
    easy_apply_to_job(driver, job_url, output_file)
    