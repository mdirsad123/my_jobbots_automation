"""
python noukrigulf_job_bot/main.py
python -m noukrigulf_job_bot.main
"""

import os
import re
import importlib.util
import hashlib
from datetime import datetime
import sys
import time
from jobbot.get_roles_responsibility_point import generate_cv_roles
from jobbot.cv_updater import update_roles_in_docx
from jobbot.easy_job_scrap import scrape_naukri_simple
from utils.clean_description import clean_job_description
from output.cached_job import cached_jobs
from jobbot.update_profile import get_driver, easy_apply_to_job

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
        experience_range = post.get("experience", "8-10 years")
        industry = post.get("company_industry", "Software development").strip()
        department = post.get("department", "IT Software").strip()
        keyword = post.get("keywords", "Software Engineer").strip()
        profile_title = post.get("title", "Software Engineer").strip()

        hashkey = generate_job_hashkey(title, company, post_date)

        if hashkey in job_applied_dict:
            print(f"Skipping job {idx+1} ({title} at {company}) - already applied.")
            continue

        if not description:
            print(f"Skipping job {idx+1} due to missing description.")
            continue

        try:
            docx_file = "noukrigulf_job_bot/input/Md_Irsad_ind.docx"
            filename_base = sanitize_filename(company)
            output_docx_file = os.path.join(output_dir, f"Md_Irsad_{filename_base}_cv.docx")

            cleaned = clean_job_description(description)
            result = generate_cv_roles(cleaned, docx_file)
            print(result)

            roles_path = os.path.join(output_dir, "generated_roles.py")
            spec = importlib.util.spec_from_file_location("generated_roles", roles_path)
            updated_roles_module = importlib.util.module_from_spec(spec)
            sys.modules["generated_roles"] = updated_roles_module
            spec.loader.exec_module(updated_roles_module)
            updated_roles = updated_roles_module.updated_roles
            summary = updated_roles["Summary"]
            skills_list = updated_roles["[DYNAMIC TECHNOLOGIES LIST 1]"]

            # final_cv_path = update_roles_in_docx(docx_file, updated_roles, output_docx_file)
            # print(f"Updated CV saved: {output_docx_file}")

            easy_apply_to_job(driver, job_url, updated_roles, experience_range, skills_list, industry, department, keyword, summary, profile_title)
            print(f"Applied to: {title} at {company}")

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
