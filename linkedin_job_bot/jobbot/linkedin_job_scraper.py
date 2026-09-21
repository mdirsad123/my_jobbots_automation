"""
python -m linkedin_job_bot.jobbot.linkedin_job_scraper
"""

import re
import time
from datetime import datetime
import urllib.parse
import json
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from utils.debbuger_port_driver import get_driver

# CACHE_FILE = "output/cached_jobs.py"
output_cache_file = Path(__file__).resolve().parent.parent / "output" / "cached_job.py"
output_cache_file.parent.mkdir(parents=True, exist_ok=True)

# ALLOWED_TITLES = [
#     "python developer", "pyspark developer", "data engineer",
#     "aws python developer", "aws data engineer", "ai engineer",
#     "full stack ai engineer", "full stack data scientist"
# ]
ALLOWED_TITLES = [
    "python developer", "data engineer", "AI engineer",
]

# Build LinkedIn search URL
def build_search_url():
    base_url = "https://www.linkedin.com/jobs/search/"
    keywords = " OR ".join([f'"{title}"' for title in ALLOWED_TITLES])
    params = {
        "keywords": keywords,
        "location": "India",
        # "f_TPR": "r604800",  # Past week
        "f_TPR": "r86400",   # Past 24 hours (86400 seconds)
        "f_WT": "1,2,3",         # Remote
        "f_EA": "true",      # Easy Apply
        "f_AL": "true",      # Application Link
        "sortBy": "DD"
    }
    query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    return f"{base_url}?{query_string}"

# Hashtag generator
def generate_hashtags(title, location):
    tags = set(f"#{w}" for w in re.findall(r'\w+', title.lower()))
    if location:
        tags.add(f"#{location.lower().replace(' ', '')}")
    # tags.add("#remote")
    return " ".join(sorted(tags))

# Parse job description and email
def extract_job_details(driver, job_url):
    driver.get(job_url)
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    desc_div = (
        soup.find("div", class_="show-more-less-html__markup") or
        soup.find("div", class_="description__text") or
        soup.find("div", {"id": "job-details"})
    )
    description = desc_div.get_text(separator="\n", strip=True) if desc_div else "N/A"
    emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", description)
    email = emails[0] if emails else "N/A"
    return description, email

# Parse job card into structured data
def clean_title(title: str) -> str:
    
    # Detect if the title is duplicated (exact or partial)
    mid = len(title) // 2
    for i in range(5, mid):  # Skip short strings, start from length 5
        prefix = title[:i]
        repeat = title[i:2*i]
        if prefix == repeat:
            return title[i:]
    return title


def parse_job_card(driver, job, idx):
    title_tag = job.find("a", class_="job-card-container__link")
    raw_title = " ".join(title_tag.stripped_strings) if title_tag else "N/A"
    title = clean_title(raw_title)
    normalized_title = title.lower().strip()

    company_tag = job.find("span", dir="ltr")
    company = company_tag.get_text(strip=True) if company_tag else "N/A"

    location_tag = job.find("ul", class_="job-card-container__metadata-wrapper")
    location = location_tag.find("span", dir="ltr").text.strip() if location_tag else "N/A"

    job_url = f"https://www.linkedin.com{title_tag['href']}" if title_tag and title_tag.get("href") else "N/A"
    post_date = datetime.now().strftime("%Y-%m-%d")

    for allowed in ALLOWED_TITLES:
        if allowed in normalized_title:
            desc, email = extract_job_details(driver, job_url)
            return {
                "title": title,
                "company": company,
                "location": location,
                "url": job_url,
                "post_date": post_date,
                "hashtags": generate_hashtags(title, location),
                "description": desc,
                "email": email
            }
    return None


def scroll_and_collect_jobs(driver, wait, scroll_pause_time=2, max_scrolls=5):
    last_height = driver.execute_script("return document.body.scrollHeight")

    for scroll in range(max_scrolls):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

# Main scraping logic
def scrape_linkedin_jobs():
    driver = get_driver()
    wait = WebDriverWait(driver, 20)
    job_data = []

    try:
        driver.get(build_search_url())
        wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "job-card-container")))
        scroll_and_collect_jobs(driver, wait)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        job_cards = soup.find_all('div', class_='job-card-container')

        for idx, job in enumerate(job_cards, start=1):
            try:
                result = parse_job_card(driver, job, idx)
                if result:
                    job_data.append(result)
            except Exception as e:
                print(f"❌ Error in job {idx}: {e}")
    finally:
        driver.quit()

    # Cache to file
    cache_to_python_file(job_data)
    return "LinkedIn jobs scraping completed and cached."

# Cache scraped job data to a Python file
def cache_to_python_file(job_data, filename=output_cache_file):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Auto-generated cached job data\n")
        f.write("cached_jobs = ")
        json.dump(job_data, f, indent=2, ensure_ascii=False)

# Run script
if __name__ == "__main__":
    jobs = scrape_linkedin_jobs()
    
    

