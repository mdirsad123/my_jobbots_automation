"""
python -m linkedin.runners.chatgpt_cv_generator

Options:
    --dry-run  Prepare attachments/prompts without sending messages.
    --force    Resubmit roles already marked as sent in today's log.

This runner determines the date in India (IST) automatically on EVERY run.
It delegates all browser, Project URL, and JD attachment behavior to
linkedin.services.chatgpt_cvs_generator.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Layout: <project_root>/linkedin/runners/chatgpt_cv_generator.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from linkedin.services.chatgpt_cvs_generator import main as service_main

# India Standard Time (UTC+05:30); no extra tzdata package required on Windows.
IST = timezone(timedelta(hours=5, minutes=30))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Open/fill role chats without clicking Send",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Resend roles already logged as sent for today",
    )
    args = parser.parse_args(argv)

    today_date = datetime.now(IST).strftime("%Y-%m-%d")
    daily_folder = (
        PROJECT_ROOT / "job_profile" / "specific" / "company" / today_date
    )

    print("=" * 60)
    print("ChatGPT CV generation runner")
    print(f"Today's date (IST): {today_date}")
    print(f"Daily JD folder:    {daily_folder}")
    print("=" * 60)

    if not daily_folder.is_dir():
        print(
            "ERROR: Today's JD directory does not exist. "
            "Run the JD scraper/grouping step first.\n"
            f"Expected: {daily_folder}",
            file=sys.stderr,
        )
        return 1

    service_args = [str(daily_folder)]
    if args.dry_run:
        service_args.append("--dry-run")
    if args.force:
        service_args.append("--force")

    # The service's main() expects a list of CLI arguments, NOT just a date.
    # It returns an exit code; the runner propagates it to the terminal.
    result = service_main(service_args)
    if result == 0:
        print("\nChatGPT CV submission pass finished; chats can continue generating.")
    else:
        print("\nSome CV requests failed; check the service output and submission log.")
    return int(result or 0)


if __name__ == "__main__":
    sys.exit(main())
