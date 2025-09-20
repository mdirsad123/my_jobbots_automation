"""
python noukrigulf_job_bot/jobbot/update_profile.py
python -m noukrigulf_job_bot.jobbot.update_profile
"""

import time
import os, sys
import pyautogui
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
import importlib.util
from utils.debbuger_port_driver import get_driver

def update_profile_section(driver, wait, industry, department, keyword, summary, profile_title):
    print("Starting profile field updates...")

    # Map field names to their edit and input XPaths
    section_map = {
        "industry": {
            "edit_xpath": "//div[@id='customSection36010755']//div[contains(@class,'custom-section-item')]//button[@class='ng-link edit-cta']",
            "input_xpath": "//div[@class='ql-editor']"
        },
        "department": {
            "edit_xpath": "//div[@id='customSection36010757']//div[contains(@class,'custom-section-item')]//button[@class='ng-link edit-cta']",
            "input_xpath": "//div[@class='ql-editor']"
        },
        "keyword": {
            "edit_xpath": "//div[@id='customSection36010765']//div[contains(@class,'custom-section-item')]//button[@class='ng-link edit-cta']",
            "input_xpath": "//div[@class='ql-editor']"
        },
        "summary": {
            "edit_xpath": "//section[@id='profileSummary360']//button[@class='ng-link edit-cta fr']",
            "input_xpath": "//div[@class='ql-editor']"
        },
        "profile_title": {
            "edit_xpath": "//div[@class='experiences']//div[1]//div[1]//button[1]",
            "input_xpath": "//input[@id='designation']"
        }
        
    }

    # Input values map
    values = {
        "industry": industry,
        "department": department,
        "keyword": keyword,
        "summary": summary,
        "profile_title": profile_title
    }

    for field in ["industry", "department", "keyword", "summary", "profile_title"]:
        try:
            print(f"Updating: {field}")

            # Click edit button
            edit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, section_map[field]["edit_xpath"])))
            edit_btn.click()
            time.sleep(1)

            # Find input box
            input_box = wait.until(EC.visibility_of_element_located((By.XPATH, section_map[field]["input_xpath"])))
            input_box.click()
            time.sleep(0.5)

            # Clear existing content
            input_box.send_keys(Keys.CONTROL, 'a')
            input_box.send_keys(Keys.BACKSPACE)
            time.sleep(0.5)

            # Enter new value
            input_box.send_keys(values[field])
            print(f"Updated {field} to: {values[field]}")

            # Click Save
            save_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Save']")))
            save_btn.click()
            print(f"Saved {field}")
            time.sleep(2)

        except Exception as e:
            print(f"Failed to update {field}: {str(e)}")


def download_updated_cv(driver, wait, output_path):
    """
    Download the updated CV from the profile page.
    """
    try:
        print("Downloading updated CV...")
        
        # Click on download CV button
        download_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[@class='download-txt']")))
        download_button.click()
        
        # Wait for download to complete
        time.sleep(2)  # wait for file dialog to open

        # Step 3: Type file path and press Enter
        pyautogui.write(output_path)
        time.sleep(2)
        pyautogui.press('enter')
        time.sleep(1)
        time.sleep(1.5)  # Wait for dialog to appear
        pyautogui.press('left')   # Move from 'No' to 'Yes'
        time.sleep(0.3)
        pyautogui.press('enter')  # Confirm overwrite
        
        print("CV downloaded successfully.")
    
    except TimeoutException:
        print("Download button not found or timed out.")
    
    
    
    
def easy_apply_to_job(driver, job_url, updated_roles, experience_range, skills_list, industry, department, keyword, summary, profile_title) -> str:
    wait = WebDriverWait(driver, 20)

    try:
        # Step 1: Go to profile and upload resume
        profile_url = "https://www.naukrigulf.com/jobseeker/resume-maker?edit=false&fieldName=&section=&subSection="
        driver.get(profile_url)
        print("Opened CV page.")
        time.sleep(1)

        # enter experience  
            
        max_experience = max(map(int, experience_range.split("Years")[0].split("-")))
        experience = 2 if max_experience > 2 else max_experience
        print(f"Parsed max experience: {experience}")

        # Fill the experience input field dynamically
        exp_input = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@id='totalExperience']")))
        exp_input.clear()
        exp_input.send_keys(str(experience))
        print(f"Entered total experience: {experience}")
        
        time.sleep(2)
        key_skill_edit_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//section[@id='keyskills']//button[@class='ng-link edit-cta fr']")))
        key_skill_edit_btn.click()
        print("Clicked on Key Skills Edit button.")
        time.sleep(2)  # Let the input load
        
        # remove existing_skills 
        while True:
            skills = driver.find_elements(By.XPATH, "//span[contains(@class, 'selection-item')]/span[@class='ico tag-cross']")
            if not skills:
                break

            try:
                skill = skills[0]  # Always remove the first one
                driver.execute_script("arguments[0].click();", skill)
                time.sleep(0.3)
            except Exception as e:
                print(f"Error while removing skill: {e}")
                break

        # Step 2: Enter key skills one by one
        skills_list = [s.strip() for s in skills_list.split(",") if s.strip()]

        # Find the visible keyskills input field (not hidden one)
        input_field = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@id='keyskillsEdit']")))

        for skill in skills_list:
            input_field.clear()
            input_field.send_keys(skill) 
            time.sleep(0.5)  # wait for dropdown to appear
            input_field.send_keys(Keys.ARROW_DOWN)
            input_field.send_keys(Keys.ENTER)
            print(f"Entered skill: {skill}")
            time.sleep(0.4)  # wait between entries to avoid skipping
            
        
        save_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Save']")))
        save_button.click()
    
        update_profile_section(driver, wait, industry, department, keyword, summary, profile_title)
        time.sleep(2)
        
        # update_all_projects(driver, wait, updated_roles)
        # time.sleep(2)
        
        # download upated cv
        # download_updated_cv(driver, wait, output_path)
        # time.sleep(2)
        # Step 2: Open job URL
        driver.get(job_url)
        print(f"Opened job URL: {job_url}")
        time.sleep(2)

        # Step 3: Click Easy Apply
        apply_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='jd-header ng-box-pure']//button[@class='ng-btn jd-button blue'][normalize-space()='Easy Apply']")))
        apply_button.click()
        print("Clicked Easy Apply button.")

        return "Job applied successfully!"

    except Exception as e:
        print(f"Error during job apply: {str(e)}")
        return "Failed: Error occurred"

def update_project(driver, wait, project_key, updated_roles):
    try:
        print(f"Updating project: {project_key}")

        xpath_map = {
            "Project #1 – Subscription Milestone": {
                "edit_xpath": "//div[@class='experiences']//div[1]//div[1]//button[1]",
                "input_xpath": "//div[@id='jobProfile']//div[contains(@class,'ql-editor')]"
            },
            "Project #2 – Insights Content": {
                "edit_xpath": "//div[@class='experiences']//div[2]//div[1]//button[1]",
                "input_xpath": "//div[@id='jobProfile']//div[contains(@class,'ql-editor')]"
            },
            "Project #3 – MQR": {
                "edit_xpath": "//div[@class='experiences']//div[3]//div[1]//button[1]",
                "input_xpath": "//div[@id='jobProfile']//div[contains(@class,'ql-editor')]"
            }
        }

        if project_key not in xpath_map:
            print(f"No XPaths mapped for: {project_key}")
            return

        edit_xpath = xpath_map[project_key]["edit_xpath"]
        input_xpath = xpath_map[project_key]["input_xpath"]

        # Click Edit
        edit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, edit_xpath)))
        edit_btn.click()
        time.sleep(1)

        # Scroll & Get Input Box
        input_box = wait.until(EC.visibility_of_element_located((By.XPATH, input_xpath)))
        driver.execute_script("arguments[0].scrollIntoView(true);", input_box)
        time.sleep(0.5)

        # Clear old content
        input_box.click()
        input_box.send_keys(Keys.CONTROL, 'a')
        input_box.send_keys(Keys.BACKSPACE)
        time.sleep(1)

        # Type updated content
        points = updated_roles[project_key]
        for key in sorted(points.keys()):
            input_box.send_keys(f"• {points[key]}\n")
            time.sleep(0.1)

        print(f"Finished updating: {project_key}")

        # Click Save
        save_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Save']")))
        save_button.click()
        time.sleep(2)

    except Exception as e:
        print(f"Error updating {project_key}: {e}")
        
def update_all_projects(driver, wait, updated_roles):
    wait = WebDriverWait(driver, 20)

    profile_url = "https://www.naukrigulf.com/jobseeker/resume-maker?edit=false&fieldName=&section=&subSection="

    for project_key in updated_roles:
        if project_key.startswith("Project"):
            # Reload page before every project update to get fresh DOM
            driver.get(profile_url)
            print(f"Reloaded CV page for: {project_key}")
            time.sleep(2)

            update_project(driver, wait, project_key, updated_roles)
                 
if __name__ == "__main__":
    driver = get_driver()
    job_url = "https://www.naukrigulf.com/business-analyst-data-scientist-jobs-in-dubai-uae-in-albatha-holding-3-to-8-years-n-cd-141063-jid-140725000249"
    
    output_dir = "noukrigulf_job_bot"
    roles_path = os.path.join(output_dir, "output", "generated_roles.py")
    
    spec = importlib.util.spec_from_file_location("generated_roles", roles_path)
    updated_roles_module = importlib.util.module_from_spec(spec)
    sys.modules["generated_roles"] = updated_roles_module
    spec.loader.exec_module(updated_roles_module)
    updated_roles = updated_roles_module.updated_roles
    
    experience_range = "8 - 12 Years"
    skills_list = "python, deployment, pip, os, orm, docker, jenkins, ci/cd, kubernetes, aws, cloud, azure, gcp, terraform, bash, git, github, environment, data science, ai, ml, model, ner, mlops"
    industry = "RecruitmentPlacement FirmExecutive Search"
    department = "Engineering"
    keyword = "Lead DevOps / MLOps Engineer (AzureTerraform)"
    
    output_path = r"C:\Users\erirs\projects\ird-projects\my_pyautomation\noukrigulf_job_bot\output\Md_Irshad_fair_value_consultancy_4_cv_2025-07-17.pdf"
    summary = updated_roles["Summary"]
    profile_title = "software engineer"
    result = easy_apply_to_job(driver, job_url, updated_roles, experience_range, skills_list, industry, department, keyword, summary, profile_title, output_path)
    
    print(result)