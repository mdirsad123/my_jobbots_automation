"""
python noukrigulf_job_bot/jobbot/job_easy_applier.py
python -m noukrigulf_job_bot.jobbot.job_easy_applier
"""

import time
import pyautogui
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from utils.debbuger_port_driver import get_driver

def easy_apply_to_job(driver, job_url: str, resume_path: str) -> str:
    wait = WebDriverWait(driver, 20)

    try:
        # Step 1: Go to profile and upload resume
        profile_url = "https://www.naukrigulf.com/mnj/userProfile/myCV?source=gnbHeader"
        driver.get(profile_url)
        print("Opened profile page.")
        time.sleep(1)
        # click cv option
        cv_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='CV']"))
        )
        cv_button.click()
        print("Clicked 'CV' button successfully.")
        time.sleep(2)
        # Wait for upload CV button
        upload_label = wait.until(EC.presence_of_element_located((By.XPATH, "//label[normalize-space()='Update CV']")))
        upload_label.click()
        time.sleep(2)  # wait for file dialog to open

        # Step 3: Type file path and press Enter
        pyautogui.write(resume_path)
        time.sleep(1)
        pyautogui.press('enter')
        time.sleep(3) 

        # Step 2: Open job URL
        driver.get(job_url)
        print(f"Opened job URL: {job_url}")
        time.sleep(2)

        # ✅ Check if already applied (for NaukriGulf)
        try:
            already_applied_element = driver.find_element(By.XPATH, "//p[@class='jd-button applied-text']")
            if already_applied_element and "already applied" in already_applied_element.text.lower():
                print("⏭️ Already applied. Skipping this job.")
                return "⏭️ Skipped: Already applied"
        except:
            # Element not found – safe to apply
            pass

        # Step 3: Click Easy Apply
        apply_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='jd-header ng-box-pure']//button[@class='ng-btn jd-button blue'][normalize-space()='Easy Apply']")))
        apply_button.click()
        print("Clicked Easy Apply button.")

        return "✅ Job applied successfully!"

    except TimeoutException as e:
        print(f"⏰ Timeout while applying: {str(e)}")
        return "❌ Failed: Timeout"

    except Exception as e:
        print(f"🚨 Error during job apply: {str(e)}")
        return "❌ Failed: Error occurred"

if __name__ == "__main__":
    driver = get_driver()
    job_url = "https://www.naukrigulf.com/senior-data-engineer-jobs-in-dubai-uae-in-vss-5-to-10-years-n-cd-281664-jid-260625000479"
    resume_path = r"C:\Users\erirs\projects\ird-projects\my_pyautomation\noukrigulf_job_bot\output\Md_Irshad_wipro_2_cv_2025-06-23.pdf"  # Use full path to PDF
    result = easy_apply_to_job(driver, job_url, resume_path)
    print(result)