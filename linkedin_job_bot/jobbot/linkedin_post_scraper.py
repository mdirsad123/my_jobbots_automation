"""
python -m linkedin_job_bot.jobbot.linkedin_post_scraper
"""

import time
import re
import json
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from pathlib import Path
import os
import sys
from datetime import datetime
from collections import Counter
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from utils.debbuger_port_driver import get_driver

output_cache_file = Path(__file__).resolve().parent.parent / "output" / "cached_post.py"
output_cache_file.parent.mkdir(parents=True, exist_ok=True)

def build_post_search_url(title: str) -> str:
    # date_range = "past-week"
    date_range = "past-24h"
    
    encoded_keywords = urllib.parse.quote(f"{title}")
    # return (
    #     f"https://www.linkedin.com/search/results/content/"
    #     f"?datePosted=%22{date_range}%22"
    #     f"&keywords={encoded_keywords}"
    # )
    return (
        f"https://www.linkedin.com/search/results/content/"
        f"?contentType=%22jobs%22&datePosted=%22{date_range}%22"
        f"&keywords={encoded_keywords}&origin=FACETED_SEARCH&sid=Orl&sortBy=%22date_posted%22"
    )

def extract_email(text):
    match = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return match[0] if match else "N/A"

def extract_job_title_from_post_text(post_text: str, allowed_titles: list[str]) -> str:
    """
    Extracts the job title from the LinkedIn post text block.
    Falls back to allowed title if nothing is found.
    """
    lines = [line.strip() for line in post_text.split("\n") if line.strip()]
    for idx, line in enumerate(lines):
        if line.lower().startswith("job by") and idx > 0:
            prev_line = lines[idx - 1].strip()
            if 3 <= len(prev_line) <= 80:  # Reasonable job title length
                return prev_line
    # fallback
    for title in allowed_titles:
        if title.lower() in post_text.lower():
            return title.title()
    return "Unknown"

def wait_for_posts_with_retry(driver, wait, title, max_retries=1, delay=2):
    for attempt in range(max_retries):
        try:
            time.sleep(1)
            page_text = driver.page_source.lower()
            if "no results found" in page_text or "try shortening" in page_text:
                print(f"No results for #{title}")
                return False
            return True
        except Exception as e:
            print(f"Retry {attempt+1}/{max_retries} failed: {e}")
            time.sleep(delay)
    return False

def generate_hashtags(description):
    pattern1 = r"#\w+"
    pattern2 = r"hashtag\s*#\s*([a-zA-Z0-9_]+)"
    tags = set(re.findall(pattern1, description.lower()))
    tags.update(f"#{tag.lower()}" for tag in re.findall(pattern2, description))
    # tags.add("#remote")
    return " ".join(sorted(tags))

def extract_poster_name(post_text):
    lines = post_text.split("\n")
    
    # Filter probable name lines: capitalized words with 2–3 tokens
    name_candidates = [line.strip() for line in lines if 2 <= len(line.strip().split()) <= 4 and line.istitle()]
    
    # Count how frequently names appear
    name_freq = Counter(name_candidates)
    
    # Sort by frequency and ignore common phrases
    ignore_list = ["Feed post", "Follow", "View job", "Like", "Comment", "Repost", "Send"]
    filtered = [name for name in name_freq if name not in ignore_list]
    
    return filtered[0] if filtered else "N/A"

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

def contains_allowed_title(description: str) -> bool:
    Filter_ALLOWED_TITLES = [
        "Python Developer", "Data Engineer", "Devops Engineer", "Data Analyst",
        "Machine Learning Engineer", "AI Engineer", "AI Agent Engineer", "Agentic AI", "Generative AI", 
        "AI Systems Engineer", "MLops", "AI Developer", "Data Scientist","cloud",
        "Backend Engineer", "Backend Developer", "devops",
        "backend", "pythonjobs", "machinelearning", "datascience",
        "dataengineer", "dataengineering", "awsdataengineer", "bigdata"
    ]
    
    desc_lower = description.lower()
    desc_no_space = desc_lower.replace(" ", "")
    
    for title in Filter_ALLOWED_TITLES:
        title_lower = title.lower()
        title_no_space = title_lower.replace(" ", "")
        
        # ✅ Match both space-preserved and space-removed versions
        if title_lower in desc_lower or title_no_space in desc_no_space:
            return True
    return False


def scrape_linkedin_posts() -> str:
    allowed_titles = ["python"]
    driver = get_driver()
    wait = WebDriverWait(driver, 20)
    posts_cache = []
    tags = ["jobs"]
    allowed_titles = ["pythondeveloper", "dataengineer", "datascientist", "awsdataengineer", "datascience", "dataengineering", "machinelearning", "pythonjobs", "bigdata", "backend", "devops", "cloud"]
    seen_emails = set()
    for title in allowed_titles:
        url = build_post_search_url(title)
        print(f"Searching: {url}")
        driver.get(url)

        # Check if "No results found" message is present
        no_results_elem = driver.find_elements(By.XPATH, "//h2[normalize-space()='No results found']")
        if no_results_elem:
            print(f"No results for #{title}. Skipping...")
            continue
        
        # Then scroll only if results are found
        for _ in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        try:
            see_more_buttons = driver.find_elements(By.XPATH, "//button[contains(., '...see more')]")
            for btn in see_more_buttons:
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(0.5)
        except Exception as e:
            print("Skipping see more buttons: %s", e)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        posts = soup.select("div.feed-shared-update-v2")
        print(f"Found {len(posts)} posts for #{title}")
        for idx, post_div in enumerate(posts, 1):
            try:
                post_text = post_div.get_text(separator="\n", strip=True)
                email = extract_email(post_text)
                
                if email in seen_emails:
                    print(f"Duplicate email found, skipping: {email}")
                    continue
                
                # Skip if stop keywords are found
                if contains_blocked_keywords(post_text):
                    print(f"Skipping job (not matched allowed title): {title}")
                    continue

                # Skip if not allowed
                if not contains_allowed_title(post_text):
                    print(f"Skipping job (not matched allowed title): {title}")
                    continue

                if email != "N/A" and any(t in post_text.lower() for t in allowed_titles):
                    # Extract company from email domain
                    match = re.search(r'@([a-zA-Z0-9.-]+)\.com', email)
                    company = match.group(1).split('.')[-1] if match else "unknown"
                    
                    job_title = extract_job_title_from_post_text(post_text, allowed_titles)

                    # ✅ Try to extract post date from the post_div (fallback = current date)
                    date_span = post_div.select_one("span.feed-shared-actor__sub-description > span:nth-child(2)")
                    post_date = date_span.get_text(strip=True) if date_span else datetime.now().strftime("%Y-%m-%d")
                    poster_name = extract_poster_name(post_text)
                    posts_cache.append({
                        "url": url,
                        "email": email,
                        "company": company.lower(),
                        "job_title": job_title,
                        "job_description": post_text[:1000],
                        "hashtags": generate_hashtags(post_text),
                        "post_date": post_date,
                        "job_poster_by": poster_name
                    })
                    seen_emails.add(email)

            except Exception as e:
                print(f"Failed post {idx}: {e}")

    driver.quit()

    # Save to Python cache file
    with open(output_cache_file, "w", encoding="utf-8") as f:
        f.write("# Auto-generated LinkedIn post cache\n")
        f.write("posts_data = ")
        f.write(json.dumps(posts_cache, indent=4, ensure_ascii=False))

    print(f"Saved {len(posts_cache)} posts to {output_cache_file}")
    return "LinkedIn post scraping completed and cached."

# ✅ Allow command-line run
if __name__ == "__main__":
    msg = scrape_linkedin_posts()
    print(msg)
