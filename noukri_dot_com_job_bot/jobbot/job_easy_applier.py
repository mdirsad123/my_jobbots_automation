"""
python noukri_dot_com_job_bot/jobbot/job_easy_applier.py
python -m noukri_dot_com_job_bot.jobbot.job_easy_applier
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
from selenium.webdriver.common.keys import Keys
from utils.debbuger_port_driver import get_driver

def profile_update(driver, wait, industry, department, category, role): 
    driver.get("https://www.naukri.com/mnjuser/profile?id=&altresid")
    time.sleep(2)
    try:
        # Scroll to Career section
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.7);")
        time.sleep(2)

        # Click Edit button
        career_edit_btn = wait.until(EC.element_to_be_clickable((
            By.XPATH, "//div[@class='desiredProfile']//span[contains(@class,'edit icon')]"
        )))
        career_edit_btn.click()
        time.sleep(2)

        # --- Fill Industry ---
        industry_input = wait.until(EC.element_to_be_clickable((By.ID, "industryFor")))
        industry_input.clear()
        industry_input.send_keys(industry)
        time.sleep(1)
        industry_input.send_keys(Keys.ARROW_DOWN)
        industry_input.send_keys(Keys.ENTER)
        time.sleep(2)

        # --- Fill Department ---
        dept_input = wait.until(EC.element_to_be_clickable((By.ID, "fareaDroopeFor")))
        dept_input.clear()
        dept_input.send_keys(department)
        time.sleep(1)
        dept_input.send_keys(Keys.ARROW_DOWN)
        dept_input.send_keys(Keys.ENTER)
        time.sleep(2)

        # --- Fill Role Category ---
        category_input = wait.until(EC.element_to_be_clickable((By.ID, "roleCategoryDroopeFor")))
        category_input.clear()
        category_input.send_keys(category)
        time.sleep(1)
        category_input.send_keys(Keys.ARROW_DOWN)
        category_input.send_keys(Keys.ENTER)
        time.sleep(2)

        # --- Fill Job Role ---
        role_input = wait.until(EC.element_to_be_clickable((By.ID, "roleDroopeFor")))
        role_input.clear()
        role_input.send_keys(role)
        time.sleep(1)
        role_input.send_keys(Keys.ARROW_DOWN)
        role_input.send_keys(Keys.ENTER)
        time.sleep(2)

        # --- Save Changes ---
        save_btn = wait.until(EC.element_to_be_clickable((By.ID, "saveDesiredProfile")))
        save_btn.click()
        time.sleep(2)
    except:
            # Element not found, safe to proceed
            pass

    print("Fields filled and dropdown selections made.")

def update_skill(driver, wait, skills_list):
    
    driver.get("https://www.naukri.com/mnjuser/profile?id=&altresid")
    time.sleep(2)
    
    # Step 1: Click edit on "Key Skills"
    key_skill_edit_btn = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//div[@id='lazyKeySkills']//span[@class='edit icon']")))
    key_skill_edit_btn.click()
    time.sleep(2)

    # Step 2: Remove existing skills
    while True:
        remove_buttons = driver.find_elements(By.XPATH, "//a[@class='material-icons close']")
        if not remove_buttons:
            break
        try:
            driver.execute_script("arguments[0].click();", remove_buttons[0])
            time.sleep(0.3)
        except Exception as e:
            print(f"Error while removing skill: {e}")
            break

    # Step 3: Enter new skills
    input_field = wait.until(EC.element_to_be_clickable((By.ID, "keySkillSugg")))

    for skill in skills_list:
        input_field.clear()
        input_field.send_keys(skill)
        time.sleep(0.5)  # Short wait for suggestions
        input_field.send_keys(',')
        time.sleep(1)

    # Step 4: Click save button
    save_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@id='saveKeySkills']")))
    save_button.click()

    print("✅ Key skills updated successfully.")        

def easy_apply_to_job(driver, job_url: str, skills_list, industry, department, category, role) -> str:
    wait = WebDriverWait(driver, 10)

    try:
        
        # update_skill(driver, wait, skills_list)
        
        time.sleep(1)
        
        # profile_update(driver, wait, industry, department, category, role)
        
        time.sleep(1)
        driver.get(job_url)
        time.sleep(1)
        
        # ✅ Check if already applied
        try:
            already_applied = driver.find_element(By.XPATH, "//span[@id='already-applied']")
            if already_applied and "applied" in already_applied.text.lower():
                print("⏭️ Already applied. Skipping this job.")
                return "⏭️ Skipped: Already applied"
        except:
            # Element not found, safe to proceed
            pass

        # Step 3: Click Easy Apply
        apply_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@class='styles_jhc__apply-button-container__5Bqnb']//button[@id='apply-button']")
        ))
        
        apply_button.click()
        print("✅ Clicked Easy Apply button.")

        return "✅ Job applied successfully!"

    except TimeoutException as e:
        print(f"⏰ Timeout while applying: {str(e)}")
        return "❌ Failed: Timeout"

if __name__ == "__main__":
    driver = get_driver()
    job_url = "https://www.naukri.com/job-listings-software-development-engineer-1-intellihealth-solutions-bengaluru-mumbai-all-areas-2-to-3-years-150725032390"
    
    skills_list = "python, deployment, pip, os, orm, docker, jenkins, ci/cd, kubernetes, aws, cloud, azure, gcp, terraform, bash, git, github, environment, data science, ai, ml, model, ner, mlops"
    industry = "IT Services & Consulting"
    department = "Engineering - Software & QA"
    category = "Software Development"
    role = "Software Development - Other",
    
    result = easy_apply_to_job(driver, job_url, skills_list, industry, department, category, role)
    print(result)