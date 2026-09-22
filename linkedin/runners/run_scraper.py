"""
python -m linkedin.runners.run_scraper
"""

import sys
import os
import argparse

# Fix project path
sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../..")
    )
)

from linkedin.services.scraper_service import scrape_feed_posts
from linkedin.services.find_similar_jobs import group_and_save_roles
from linkedin.services.copy_group_role_specific_data import copy_group_role_specific_data
from utils.debbuger_port_driver import get_driver

from datetime import datetime

def main():
    parser = argparse.ArgumentParser(
        description="Run LinkedIn scraper and group today's scraped jobs"
    )
    parser.add_argument(
        "--mode",
        choices=["feed", "easy", "all"],
        default="feed",
        help="Scrape mode",
    )
    args = parser.parse_args()

    driver = get_driver()

    try:
        if args.mode in ["feed", "all"]:
            print("Starting Feed Post Scraper...")

            scraped_count = scrape_feed_posts(driver)

            print(
                f"Feed scraping completed. "
                f"New jobs scraped: {scraped_count}"
            )

            # The scraper has now saved today's jobs to:
            # output/scrap/YYYY-MM-DD.json
            #
            # Next, read that JSON and create role-wise grouped .txt files.
            print("Starting Role Grouping...")

            grouped_summary = group_and_save_roles(
                today_only=True
            )

            
            if grouped_summary:
                print(
                    f"Role grouping completed. "
                    f"Groups created: {len(grouped_summary)}"
                )

                for role, details in grouped_summary.items():
                    print(
                        f"  - {role}: "
                        f"{details['job_count']} jobs -> "
                        f"{details['file']}"
                    )
            else:
                print(
                    "Role grouping completed, but no groups "
                    "were created."
                )

        today_date = datetime.now().strftime("%Y-%m-%d")

        copy_group_role_specific_data(
            folder_path=f"linkedin/output/grouped_jobs/{today_date}",
        )
        # Easy Apply scraper has been removed from scraper_service.py.
        # Keep this mode only for CLI compatibility.
        if args.mode == "easy":
            print(
                "Easy Apply scraper is no longer available. "
                "Only feed scraping is enabled."
            )

    finally:
        try:
            driver.quit()
        except Exception:
            pass

if __name__ == "__main__":
    main()
