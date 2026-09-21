"""
python noukri_dot_com_job_bot/main.py
python -m noukri_dot_com_job_bot.main
"""

import os
import re
import importlib.util
import hashlib
from datetime import datetime
import sys
import time
# from jobbot.get_roles_responsibility_point import generate_cv_roles
from jobbot.get_key_skill import extract_key_skills
# from jobbot.cv_updater import update_roles_in_docx
from jobbot.easy_job_scrap import scrape_naukri_simple
from utils.clean_description import clean_job_description
from output.cached_job import cached_jobs
from jobbot.job_easy_applier import easy_apply_to_job
from utils.debbuger_port_driver import get_driver

HASHKEYS_PATH = os.path.join(os.path.dirname(__file__), "output", "job_hashkeys.py")

# ------------------ Hashkey Management ------------------

def load_all_hashkeys():
    if not os.path.exists(HASHKEYS_PATH):
        return {}
    spec = importlib.util.spec_from_file_location("job_hashkeys", HASHKEYS_PATH)
    hash_module = importlib.util.module_from_spec(spec)
    sys.modules["job_hashkeys"] = hash_module
    spec.loader.exec_module(hash_module)
    return getattr(hash_module, "job_applied_hashkeys", {})

def save_all_hashkeys(job_key_dict):
    with open(HASHKEYS_PATH, "w", encoding="utf-8") as f:
        f.write("# Auto-generated job hashkey dictionary\n\n")
        f.write("job_applied_hashkeys = {\n")
        for hk, meta in sorted(job_key_dict.items()):
            title = re.sub(r'\s+', ' ', meta.get("title", "").strip().replace("'", "\\'"))
            company = re.sub(r'\s+', ' ', meta.get("company", "").strip().replace("'", "\\'"))
            posted_date = meta.get("posted_date", "")
            f.write(f"    '{hk}': {{'title': '{title}', 'company': '{company}', 'posted_date': '{posted_date}'}},\n")
        f.write("}\n\n")

def generate_job_hashkey(title, company, post_date):
    clean_title = re.sub(r'\s+', ' ', title.strip().lower())
    clean_company = re.sub(r'\s+', ' ', company.strip().lower())
    clean_post_date = post_date.strip()
    text = f"{clean_title}::{clean_company}::{clean_post_date}"
    return hashlib.md5(text.encode()).hexdigest()

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name).replace(" ", "_").lower()

# ------------------ Easy Apply Main Logic ------------------
def easy_job_main():
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    driver = get_driver()
    
    print(scrape_naukri_simple())

    time.sleep(2)
    job_applied_dict = load_all_hashkeys()
    updated_job_dict = dict(job_applied_dict)

    for idx, post in enumerate(cached_jobs):
        title = post.get("title", "").strip()
        company = post.get("company", f"Company_{idx+1}")
        post_date = post.get("posted_date", datetime.today().strftime("%Y-%m-%d"))
        job_url = post.get("url", "")
        description = post.get("description", "").strip()
        industry = post.get("industry", "IT Services & Consulting")
        department = post.get("department", "Engineering - Software & QA")
        category = post.get("category", "Software Development")
        role = post.get("role", "Software Development - Other")

        hashkey = generate_job_hashkey(title, company, post_date)

        if hashkey in job_applied_dict:
            print(f"Skipping job {idx+1} ({title} at {company}) - already applied.")
            continue

        if not description:
            print(f"Skipping job {idx+1} due to missing description.")
            continue

        try:
            cleaned_jd = clean_job_description(description)
            
            skills_list = extract_key_skills(cleaned_jd)
            
            print(f"Applied to: {title} at {company}")
            easy_apply_to_job(driver, job_url, skills_list, industry, department, category, role)
            
            time.sleep(5)

            updated_job_dict[hashkey] = {
                "title": title,
                "company": company,
                "posted_date": post_date
            }

        except Exception as e:
            print(f"Failed to process job {idx+1} ({title}): {e}")

    save_all_hashkeys(updated_job_dict)
    driver.quit()
    print(f"All applicable jobs processed. CVs saved in: {output_dir}")

# ------------------ Entry Point ------------------

if __name__ == "__main__":
    easy_job_main()
