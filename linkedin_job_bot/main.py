"""
python linkedin_job_bot/main.py
python -m linkedin_job_bot.main
"""

import os
import re
import importlib.util
import hashlib
from datetime import datetime
import sys
import time
from jobbot.linkedin_post_scraper import scrape_linkedin_posts
from output.cached_post import posts_data
from jobbot.get_roles_responsibility_point import generate_cv_roles
from jobbot.cv_updater import update_roles_in_docx
from jobbot.post_applier import apply_to_job
from utils.clean_description import clean_job_description
from jobbot.linkedin_job_scraper import scrape_linkedin_jobs
from output.cached_job import cached_jobs
from jobbot.job_easy_applier import get_driver, easy_apply_to_job

HASHKEYS_PATH = os.path.join(os.path.dirname(__file__), "output", "job_hashkeys.py")

# ------------------ Shared Hashkey Management ------------------

def load_all_hashkeys():
    if not os.path.exists(HASHKEYS_PATH):
        return {}, {}
    spec = importlib.util.spec_from_file_location("job_hashkeys", HASHKEYS_PATH)
    hash_module = importlib.util.module_from_spec(spec)
    sys.modules["job_hashkeys"] = hash_module
    spec.loader.exec_module(hash_module)
    job_keys = dict(getattr(hash_module, "job_applied_hashkeys", {}))
    post_keys = dict(getattr(hash_module, "post_applied_hashkeys", {}))
    return job_keys, post_keys

def save_all_hashkeys(job_keys, post_keys):
    with open(HASHKEYS_PATH, "w", encoding="utf-8") as f:
        f.write("# Auto-generated hashkey list\n\n")
        f.write("job_applied_hashkeys = {\n")
        for hk, meta in sorted(job_keys.items()):
            f.write(f"    '{hk}': {meta},\n")
        f.write("}\n\n")
        f.write("post_applied_hashkeys = {\n")
        for hk, meta in sorted(post_keys.items()):
            f.write(f"    '{hk}': {meta},\n")
        f.write("}\n")

def generate_post_hashkey(title, email, post_date, company, clean_desc, job_posted_by):
    text = f"{title.strip().lower()}::{email.strip().lower()}::{post_date.strip().lower()}::{company.strip().lower()}::{clean_desc.strip().lower()}::{job_posted_by.strip().lower()}"
    return hashlib.md5(text.encode()).hexdigest()

def generate_job_hashkey(title, email, post_date):
    text = f"{title.strip().lower()}::{email.strip().lower()}::{post_date.strip()}"
    return hashlib.md5(text.encode()).hexdigest()

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name).replace(" ", "_").lower()

# ------------------ Post Job Apply ------------------

def post_job_main():
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    print(scrape_linkedin_posts())

    time.sleep(2)

    job_keys, post_applied_hashkeys = load_all_hashkeys()
    updated_post_hashkeys = dict(post_applied_hashkeys)

    for idx, post in enumerate(posts_data):
        description = post.get("job_description", "").strip()
        clean_desc = clean_job_description(description)
        company = post.get("company", f"Company_{idx+1}")
        post_date = post.get('post_date') or datetime.today().strftime("%Y-%m-%d")
        post_email = post.get('email')
        job_posted_by = post.get('job_poster_by')
        title = post.get('job_title')

        if not description:
            print(f"Skipping job {idx+1} due to missing description.")
            continue

        hashkey = generate_post_hashkey(title, post_email, post_date, company, clean_desc, job_posted_by)
        if hashkey in post_applied_hashkeys:
            print(f"Skipping job {idx+1} ({company}) - already emailed.")
            continue

        try:
            docx_file = "linkedin_job_bot/input/Md_Irsad_ind.docx"
            filename_base = sanitize_filename(company).replace("unknown", "").strip("_").strip().lower()
            if not filename_base:
                output_docx_file = os.path.join(output_dir, "Md_Irsad_cv.docx")
            else:
                output_docx_file = os.path.join(output_dir, f"Md_Irsad_{filename_base}_cv.docx")

            result = generate_cv_roles(clean_desc, docx_file)
            print(result)

            roles_path = os.path.join(output_dir, "generated_roles.py")
            spec = importlib.util.spec_from_file_location("generated_roles", roles_path)
            updated_roles_module = importlib.util.module_from_spec(spec)
            sys.modules["generated_roles"] = updated_roles_module
            spec.loader.exec_module(updated_roles_module)
            updated_roles = updated_roles_module.updated_roles

            final_cv_path = update_roles_in_docx(docx_file, updated_roles, output_docx_file)
            print(f"Saved CV for {company}: {final_cv_path}")

            email_template = updated_roles['Summary']
            apply_to_job(post_email, email_template, final_cv_path, title)
            print(f"Email sent successfully to {post_email}")
            time.sleep(10)  # Avoid rate limiting
            
            # import pdb; pdb.set_trace()
            
            updated_post_hashkeys[hashkey] = {
                "title": title,  # Using company as title in post-based jobs
                "email": post_email or "Unknown",
                "post_date": post_date
            }

        except Exception as e:
            print(f"Failed to process job {idx+1} ({company}): {e}")

    save_all_hashkeys(job_keys, updated_post_hashkeys)
    print(f"All eligible HRs contacted. CVs saved in: {output_dir}")

# ------------------ Easy Apply Job ------------------

def easy_job_main():
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    driver = get_driver()
    
    print(scrape_linkedin_jobs())
    time.sleep(2)

    job_applied_hashkeys, post_keys = load_all_hashkeys()
    new_job_keys = dict(job_applied_hashkeys)

    for idx, post in enumerate(cached_jobs):
        title = post.get("title", "").strip()
        company = post.get("company", f"Company_{idx+1}")
        post_date = post.get('post_date', datetime.today().strftime("%Y-%m-%d"))
        job_url = post.get('url', "")
        description = post.get("description", "").strip()

        hashkey = generate_job_hashkey(title, company, post_date)

        if hashkey in job_applied_hashkeys:
            print(f"Skipping job {idx+1} ({title} at {company}) - already applied.")
            continue

        if not description:
            print(f"Skipping job {idx+1} due to missing description.")
            continue

        try:
            docx_file = "linkedin_job_bot/input/Md_Irsad_ind.docx"
            filename_base = sanitize_filename(company).replace("unknown", "").strip("_").strip().lower()
            if not filename_base:
                output_docx_file = os.path.join(output_dir, "Md_Irsad_cv.docx")
            else:
                output_docx_file = os.path.join(output_dir, f"Md_Irsad_{filename_base}_cv.docx")

            # output_docx_file = os.path.join(output_dir, f"Md_Irsad_{filename_base}_{idx+1}_cv_{post_date}.docx")

            cleaned = clean_job_description(description)
            result = generate_cv_roles(cleaned, docx_file)
            print(result)

            roles_path = os.path.join(output_dir, "generated_roles.py")
            spec = importlib.util.spec_from_file_location("generated_roles", roles_path)
            updated_roles_module = importlib.util.module_from_spec(spec)
            sys.modules["generated_roles"] = updated_roles_module
            spec.loader.exec_module(updated_roles_module)
            updated_roles = updated_roles_module.updated_roles

            final_cv_path = update_roles_in_docx(docx_file, updated_roles, output_docx_file)
            print(f"Updated CV saved: {output_docx_file}")

            easy_apply_to_job(driver, job_url, output_docx_file)
            print(f"Applied to: {title} at {company}")

            new_job_keys[hashkey] = {
                "title": title,
                "company": company,
                "post_date": post_date
            }

        except Exception as e:
            print(f"Failed to process job {idx+1} ({title}): {e}")

    save_all_hashkeys(new_job_keys, post_keys)
    driver.quit()
    print(f"All applicable jobs processed. CVs saved in: {output_dir}")

# ------------------ Entry Point ------------------

if __name__ == "__main__":
    post_job_main()
    time.sleep(5)  # Give some time before starting easy apply
    easy_job_main()