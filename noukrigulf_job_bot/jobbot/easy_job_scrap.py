"""
python -m noukrigulf_job_bot.jobbot.easy_job_scrap
"""

import time
from datetime import datetime, timedelta
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
import re
import os
import sys
from typing import Optional, Tuple
from datetime import datetime, timedelta
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from utils.time_calc_decorator import timeit
import importlib.util

CHROME_DRIVER_PATH = r"D:\ird-projects\my_pyautomation\ui\driver\chromedriver.exe"
# Config
NAUKRI_HOME_URL = "https://www.naukrigulf.com/mnj/userProfile/myHome?conmnj=1&showQsb=1&source="
output_cache_file = Path(__file__).resolve().parent.parent / "output" / "cached_job.py"
output_cache_file.parent.mkdir(parents=True, exist_ok=True)

ALLOWED_TITLES = ["Python Developer", "Data Engineer", "Software Engineer"]
# ALLOWED_TITLES = ["Python Developer", "Data Engineer", "Software Engineer", "Devops Engineer", "Data Scientist", "Machine Learning Engineer", "AI Engineer", "Backend Developer", "Full Stack Developer"]
# LOCATIONS = ["United Arab Emirates", "Saudi Arabia", "Dubai", "Abu Dhabi", "Riyadh", "Jeddah", "Doha", "Kuwait City", "Manama", "Amman"]
LOCATIONS = ["United Arab Emirates", "Saudi Arabia", "Dubai"]
EXPERIENCE = "2"  # Years

# Chrome with debugger port
def get_driver():
    options = Options()
    options.debugger_address = "127.0.0.1:9222"
    return webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=options)

# Cache to file
def cache_to_python_file(job_data, filename=output_cache_file):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Auto-generated cached job data\n")
        f.write("cached_jobs = ")
        json.dump(job_data, f, indent=2, ensure_ascii=False)

def parse_posted_date(date_text: str) -> str:
    date_text = date_text.strip().lower()
    today = datetime.today()

    # Match "30+ days ago"
    if re.match(r"\d+\+?\s+days?\s+ago", date_text):
        days_ago = int(re.findall(r"\d+", date_text)[0])
        return (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")

    # Match "X hrs ago"
    elif re.match(r"\d+\s+hrs?\s+ago", date_text):
        hours_ago = int(re.findall(r"\d+", date_text)[0])
        return (today - timedelta(hours=hours_ago)).strftime("%Y-%m-%d")

    # Match "X mins ago"
    elif re.match(r"\d+\s+mins?\s+ago", date_text):
        minutes_ago = int(re.findall(r"\d+", date_text)[0])
        return (today - timedelta(minutes=minutes_ago)).strftime("%Y-%m-%d")

    # Match "23 Jun" or "5 May"
    elif re.match(r"\d{1,2}\s+[a-z]{3,}", date_text):
        try:
            parsed = datetime.strptime(date_text, "%d %b")
            # Add current year
            parsed = parsed.replace(year=today.year)
            # If future date (e.g., Dec when today is Jan), assume previous year
            if parsed > today:
                parsed = parsed.replace(year=today.year - 1)
            return parsed.strftime("%Y-%m-%d")
        except:
            pass

    # Default fallback
    return today.strftime("%Y-%m-%d")

def contains_allowed_title(title: str, description: str) -> bool:
    Filter_ALLOWED_TITLES = [
        "Python Developer", "Data Engineer", "Software Engineer", "Devops Engineer", "Data Analyst",
        "Machine Learning Engineer", "AI Engineer", "AI Agent Engineer", "Agentic AI", "Generative AI", "AI Systems Engineer", "MLops", "AI Developer", "Data Scientist",
        "Backend Engineer", "Backend Developer", "Full Stack Developer", "Technical Support Specialist",
        "Database Platform", "Product Engineer"
    ]
    combined_text = f"{title} {description}".lower()
    
    for keyword in Filter_ALLOWED_TITLES:
        if keyword.lower() in combined_text:
            return True
    return False

def extract_job_metadata(full_desc: str) -> dict:
    fields = [
        "Experience", 
        "Job Location", 
        "Education", 
        "Nationality", 
        "Gender", 
        "Vacancy", 
        "Job Description", 
        "Company Industry", 
        "Department / Functional Area", 
        "Keywords"
    ]
    metadata = {}

    for i, field in enumerate(fields):
        if i < len(fields) - 1:
            next_field = fields[i + 1]
            pattern = re.compile(rf"{re.escape(field)}\n(.*?)\n{re.escape(next_field)}", re.DOTALL)
        else:
            # Last field: match until end
            pattern = re.compile(rf"{re.escape(field)}\n(.*)", re.DOTALL)

        match = pattern.search(full_desc)
        if match:
            value = match.group(1).strip()
            
            # Strip "Easy Apply" from keywords if present
            if field == "Keywords":
                value = value.split("\nEasy Apply")[0].strip()
            
            metadata[field.lower().replace(" ", "_").replace("/", "_")] = value

    return metadata

def scrape_job_description_from_url(driver, url, wait):
    original_tab = driver.current_window_handle

    # Open new tab (Selenium v4)
    driver.switch_to.new_window('tab')
    driver.get(url)
    time.sleep(1)
    try:
        desc_el = wait.until(EC.presence_of_element_located((
            By.XPATH, "//div[contains(@class,'job-details ng-box-pure')]"
        )))
        time.sleep(1)  # Wait for content to load
        
        full_desc = desc_el.text.strip()

    except Exception as e:
        print(f"❌ Failed to load job page: {e}")
        full_desc = ""
    time.sleep(1)
    # Close tab and return
    driver.close()
    driver.switch_to.window(original_tab)

    return full_desc

# Main logic
def scrape_naukri_simple():
    driver = get_driver()
    wait = WebDriverWait(driver, 20)
    job_data = []
    cutoff_date = datetime.today() - timedelta(days=2)

    try:
        driver.get(NAUKRI_HOME_URL)
        wait.until(EC.presence_of_element_located((By.ID, "qsbKey")))
        driver.find_element(By.ID, "qsbKey").send_keys(", ".join(ALLOWED_TITLES))
        driver.find_element(By.ID, "qsbLoc").send_keys(", ".join(LOCATIONS))
        driver.find_element(By.ID, "qsbExp").send_keys(EXPERIENCE)

        driver.find_element(By.XPATH, "//input[@value='Search Jobs']").click()

        wait.until(EC.presence_of_element_located((By.XPATH, "//bdi[contains(text(),'Easy Apply')]")))
        driver.find_element(By.XPATH, "//bdi[contains(text(),'Easy Apply')]").click()
        time.sleep(2) 
        
        date_sort = driver.find_element(By.XPATH, "//li[@data-value='date']")
        if "active-true" not in date_sort.get_attribute("class"):
            date_sort.click()
            time.sleep(2)  # Wait for sorting to apply

        def extract_jobs_on_page():
            # Scroll to load all jobs
            SCROLL_PAUSE_TIME = 2
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(SCROLL_PAUSE_TIME)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            # Get all job cards now
            job_cards = driver.find_elements(By.XPATH, "//div[@class='ng-box srp-tuple']")

            for idx, card in enumerate(job_cards, 1):
                try:
                    title_el = card.find_element(By.CLASS_NAME, "info-position")
                    title = title_el.text.strip()
                    url = title_el.get_attribute("href")

                    company = card.find_element(By.CLASS_NAME, "info-org").text.strip()

                    try:
                        date_text = card.find_element(By.CLASS_NAME, "time").text.strip()
                    except:
                        date_text = "N/A"
                    
                    if date_text == "N/A":
                        print(f"Skipping job {idx} (no date): {title}")
                        continue
                    
                    posted_date_str = parse_posted_date(date_text)
                    posted_date = datetime.strptime(posted_date_str, "%Y-%m-%d")
                    
                    # Skip if older than 7 days
                    if posted_date < cutoff_date:
                        continue
                    
                    full_desc = scrape_job_description_from_url(driver, url, wait)
                    
                    job_meta = extract_job_metadata(full_desc)

                    experience = job_meta.get("experience", "")
                    job_location = job_meta.get("job_location", "")
                    education = job_meta.get("education", "")
                    job_description = job_meta.get("job_description", "")
                    company_industry = job_meta.get("company_industry", "")
                    department = job_meta.get("department___functional_area", "")
                    keywords = job_meta.get("keywords", "")
                    
                    
                    # Skip if not allowed
                    if not contains_allowed_title(title, job_description):
                        print(f"Skipping job (not matched allowed title): {title}")
                        continue
                    posted_date_str2 = posted_date.strftime("%Y-%m-%d")
                    
                    job_data.append({
                        "title": title,
                        "company": company,
                        "experience": experience,
                        "job_location": job_location,
                        "education": education,
                        "description": job_description,
                        "company_industry": company_industry,
                        "department": department,
                        "keywords": keywords,
                        "url": url,
                        "posted_date": posted_date_str2
                    })

                except Exception as e:
                    print(f"Error extracting job {idx}: {e}")
                    
        # Page 1 scrape
        extract_jobs_on_page()

    finally:
        driver.quit()

    cache_to_python_file(job_data)
    return f"Done. Scraped {len(job_data)} Easy Apply jobs (posted within 7 days) and saved to cache."


# Entry point
if __name__ == "__main__":
    print(scrape_naukri_simple())
