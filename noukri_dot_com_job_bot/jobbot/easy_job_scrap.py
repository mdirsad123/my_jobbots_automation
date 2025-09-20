"""
python -m noukri_dot_com_job_bot.jobbot.easy_job_scrap
"""

import time
from datetime import datetime, timedelta
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
import re
import os
import sys
from selenium.webdriver.chrome.service import Service
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

CHROME_DRIVER_PATH = r"D:\ird-projects\my_pyautomation\ui\driver\chromedriver.exe"
# Config
NAUKRI_HOME_URL = "https://www.naukri.com/mnjuser/homepage"
output_cache_file = Path(__file__).resolve().parent.parent / "output" / "cached_job.py"
output_cache_file.parent.mkdir(parents=True, exist_ok=True)

ALLOWED_TITLES = ["Data Engineer", "Python Developer"]
# ALLOWED_TITLES = ["Python Developer", "Data Engineer", "Software Engineer", "Devops Engineer", "Data Scientist", "Machine Learning Engineer", "AI Engineer", "Backend Developer", "Full Stack Developer"]
EXPERIENCE = 2  # Years

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
        "Machine Learning Engineer", "AI Engineer", "AI Agen Engineer", "Agentic AI", "Generative AI", "AI Systems Engineer", "MLops", "AI Developer", "Data Scientist",
        "Backend Engineer", "Backend Developer", "Full Stack Developer",
        "Database Platform", "Product Engineer", "Fullstack Developer", "Full Stack Development",
        "Software Engineer", "Blockchain Developer",
    ]
    combined_text = f"{title} {description}".lower()
    
    for keyword in Filter_ALLOWED_TITLES:
        if keyword.lower() in combined_text:
            return True
    return False

def scrape_job_description_from_url(driver, url, wait):
    original_tab = driver.current_window_handle

    # Open new tab (Selenium v4)
    driver.switch_to.new_window('tab')
    driver.get(url)

    try:
        time.sleep(5)

        # Detect “Apply on company site”
        try:
            company_site_btn = driver.find_elements(By.ID, "company-site-button")
            if company_site_btn:
                print("⛔ Skipping — Company site apply detected")
                driver.close()
                driver.switch_to.window(original_tab)
                return None
        except:
            pass  # Ignore button check failure and proceed
        
        # for read more button
        try:
            read_more = driver.find_element(By.XPATH, "//a[normalize-space()='read more']")
            
            if read_more:
                driver.execute_script("arguments[0].click();", read_more)
        except:
            pass  # Ignore button check failure and proceed
        
        time.sleep(1)

        # Get full job description
        try:
            desc_el = wait.until(EC.presence_of_element_located((
                By.XPATH, "//section[contains(@class,'job-desc-container')]"
            )))
            
            full_desc = desc_el.text.strip()
        except TimeoutException:
            print("❌ Job description not found — skipping.")
            full_desc = ""

    except Exception as e:
        print(f"❌ Failed to load job page: {e}")
        full_desc = ""

    # Close tab and return
    driver.close()
    driver.switch_to.window(original_tab)

    return full_desc

def extract_job_metadata(full_desc: str) -> dict:
    metadata = {}

    # Define patterns for the new fields
    role_pattern = re.search(r"Role:\s*(.*)", full_desc)
    industry_type_pattern = re.search(r"Industry Type:\s*(.*)", full_desc)
    department_pattern = re.search(r"Department:\s*(.*)", full_desc)
    employment_type_pattern = re.search(r"Employment Type:\s*(.*)", full_desc)
    role_category_pattern = re.search(r"Role Category:\s*(.*)", full_desc)
    key_skills_pattern = re.search(r"Key Skills\s*(Skills highlighted.*?keyskills)?\s*(.*?)\nReport this job", full_desc, re.DOTALL)

    # Extract and store the values if matched
    if role_pattern:
        metadata["role"] = role_pattern.group(1).strip()
    if industry_type_pattern:
        metadata["industry_type"] = industry_type_pattern.group(1).strip()
    if department_pattern:
        metadata["department"] = department_pattern.group(1).strip()
    if employment_type_pattern:
        metadata["employment_type"] = employment_type_pattern.group(1).strip()
    if role_category_pattern:
        metadata["role_category"] = role_category_pattern.group(1).strip()
    if key_skills_pattern:
        metadata["key_skills"] = key_skills_pattern.group(2).strip().replace('\n', ', ')

    return metadata

def contains_blocked_keywords(text: str) -> bool:
    blocked_keywords = [
        r'\bjava\b',
        r'\bc#\b',
        r'\bc\+\+\b',
        r'\bangular\b',
        r'\bruby\b',
        r'\brust\b',
        r'\bdot\s*net\b',
        r'\b\.net\b',
    ]
    text_lower = text.lower()

    for pattern in blocked_keywords:
        if re.search(pattern, text_lower):
            return True  # Blocked keyword found

    return False  # No blocked keywords

# Main logic
def scrape_naukri_simple():
    driver = get_driver()
    wait = WebDriverWait(driver, 20)
    job_data = []

    try:
        driver.get(NAUKRI_HOME_URL)

        # Click the search bar to activate the input fields
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='nI-gNb-sb__main']"))).click()
        time.sleep(2)

        # Enter job roles
        role_input = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//input[@placeholder='Enter keyword / designation / companies']")
        ))
        role_input.clear()
        role_input.send_keys(", ".join(ALLOWED_TITLES))
        time.sleep(1)

        # Step 1: Click to open the experience dropdown
        exp_input = wait.until(EC.element_to_be_clickable((By.ID, "experienceDD")))
        exp_input.click()
        time.sleep(1)
        
        for _ in range(0, EXPERIENCE):
            exp_input.send_keys(Keys.ARROW_DOWN)
            time.sleep(0.5) 
        exp_input.send_keys(Keys.ENTER)
        time.sleep(1)
        
        

        

        # Click the Search button
        search_btn = driver.find_element(By.XPATH, "//span[normalize-space()='Search']")
        driver.execute_script("arguments[0].click();", search_btn)  
        
        time.sleep(1)
        
        filter_dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@id='filter-sort']//i[@class='ni-icon-arrow-down']")))
        driver.execute_script("arguments[0].click();", filter_dropdown)
        time.sleep(1)
        filter_by_date = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[normalize-space()='Date']")))
        driver.execute_script("arguments[0].click();", filter_by_date)

        # Apply salary filters
        salary_filters = [
            "//label[@for='chk-6-10 Lakhs-ctcFilter-']//i",
            "//label[@for='chk-10-15 Lakhs-ctcFilter-']//i",
            "//label[@for='chk-15-25 Lakhs-ctcFilter-']//i",
        ]

        for xpath in salary_filters:
            try:
                elem = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                driver.execute_script("arguments[0].click();", elem)
                time.sleep(1)
            except Exception as e:
                print(f"❌ Failed to click salary filter {xpath}: {e}")

        # Apply "Posted By: Company Jobs" filter
        try:
            posted_by_xpath = "//label[@for='chk-Company Jobs-jobPostType-']//i"
            posted_by_elem = wait.until(EC.element_to_be_clickable((By.XPATH, posted_by_xpath)))
            driver.execute_script("arguments[0].click();", posted_by_elem)
            time.sleep(1)
        except Exception as e:
            print(f"❌ Failed to click Company Jobs filter: {e}")

        # Select "Last 1 day" freshness
        try:
            freshness_dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[normalize-space()='Select']")))
            driver.execute_script("arguments[0].click();", freshness_dropdown)
            time.sleep(1)

            last_1_day = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[normalize-space()='Last 1 day']")))
            driver.execute_script("arguments[0].click();", last_1_day)
            time.sleep(1)
        except Exception as e:
            print(f"❌ Failed to select 'Last 1 day': {e}")

        # Wait for job results to load
        wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@class='cust-job-tuple layout-wrapper lay-2 sjw__tuple ']")))

        def extract_jobs_on_page():
            time.sleep(2)
            job_cards = driver.find_elements(By.XPATH, "//div[@class='cust-job-tuple layout-wrapper lay-2 sjw__tuple ']")
            for idx, card in enumerate(job_cards, 1):
                
                try:
                    # Extract title and URL
                    title_el = card.find_element(By.CLASS_NAME, "title")
                    title = title_el.text.strip()
                    url = title_el.get_attribute("href")

                    if contains_blocked_keywords(title):
                        print(f"Skipping job (not matched allowed title): {title}")
                        continue
                    
                    try:
                        company_el = card.find_element(By.CLASS_NAME, "comp-name")
                        company = company_el.text.strip()
                    except:
                        company = "N/A"
                        
                    # Fetch description via URL
                    full_description = scrape_job_description_from_url(driver, url, wait)
                    if full_description is None:
                        continue
                    
                    # Skip if stop keywords are found
                    if contains_blocked_keywords(full_description):
                        print(f"Skipping job (not matched allowed title): {title}")
                        continue

                    time.sleep(1)

                    job_meta = extract_job_metadata(full_description)
                    time.sleep(1)

                    role = job_meta.get("role", "")
                    industry_type = job_meta.get("industry_type", "")
                    department = job_meta.get("department", "")
                    employment_type = job_meta.get("employment_type", "")
                    role_category = job_meta.get("role_category", "")
                    key_skills = job_meta.get("key_skills", "")

                    if "Job description" in full_description:
                        full_desc = full_description.split("Job description", 1)[1].strip()

                    try:
                        date_text = card.find_element(By.CLASS_NAME, "type").text.strip()
                    except:
                        date_text = "N/A"
                    posted_date = parse_posted_date(date_text)

                    # Save result
                    job_data.append({
                        "title": title,
                        "company": company,
                        "posted_date": posted_date,
                        "url": url,
                        "role": role,
                        "industry_type": industry_type,
                        "department": department,
                        "employment_type": employment_type,
                        "role_category": role_category,
                        "key_skills": key_skills,
                        "description": full_desc
                    })
                except Exception as e:
                    print(f"❌ Error extracting job {idx}: {e}")

        # Page 1 scrape
        extract_jobs_on_page()

        # Page 2 click and scrape
        try:
            # Scroll down 80% to make pagination visible
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.8);")
            time.sleep(2)
            # Click the "Next" button to go to page 2
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[normalize-space()='Next']/parent::a"))
            )

            # Scroll into view if needed
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
            time.sleep(1)

            # Try normal click, fallback to JS click if needed
            try:
                next_button.click()
            except:
                driver.execute_script("arguments[0].click();", next_button)

            time.sleep(3)

            # Call your scraping function
            extract_jobs_on_page()

        except Exception as e:
            print(f"⚠️ Could not click next page: {e}")

        # Page 3 click and scrape
        try:
            # Scroll down 80% to make pagination visible
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.8);")
            time.sleep(2)
            # Click the "Next" button to go to page 2
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[normalize-space()='Next']/parent::a"))
            )

            # Scroll into view if needed
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
            time.sleep(1)

            # Try normal click, fallback to JS click if needed
            try:
                next_button.click()
            except:
                driver.execute_script("arguments[0].click();", next_button)

            time.sleep(3)

            # Call your scraping function
            extract_jobs_on_page()

        except Exception as e:
            print(f"⚠️ Could not click next page: {e}")
            
    finally:
        driver.quit()

    cache_to_python_file(job_data)
    return f"✅ Done. Scraped {len(job_data)} Easy Apply jobs (posted within 7 days) from 2 pages and saved to cache."



# Entry point
if __name__ == "__main__":
    print(scrape_naukri_simple())
