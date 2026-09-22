"""
python -m linkedin.services.manual_email_sender

Automatically send job-application emails for all supported role folders
inside one daily company folder.

Expected folder structure
-------------------------
job_profile/
└── specific/
    └── company/
        └── 2026_09_17/
            ├── aiengineer/
            ├── awsdataengineer/
            ├── azuredataengineer/
            └── pythondeveloper/

For every role folder that exists, the script automatically discovers:

1. EMAIL_REPLY_TEXT_PATH
   - Prefer a .txt file whose filename contains "email_reply".
   - The file must have "Subject:" as its first non-empty line.

2. JD file
   - Prefer an exact file named "jd.txt".
   - Otherwise find a .txt file containing "jd" in the filename,
     excluding the email-reply file.

3. Recipient emails
   - Read only lines beginning with:
         # Emails:
   - Extract all comma-separated email addresses from those lines.

4. CV attachment
   - Find a .pdf file whose filename contains "cv".
   - If several CV PDFs exist, prefer one containing "md_irshad_cv".
   - The script refuses to guess if more than one ambiguous CV remains.

Usage
-----
From Python:
    main(r"job_profile\specific\company\2026_09_17")

From command line:
    python manual_email_sender_automated.py "job_profile\specific\company\2026_09_17"

Environment variables
---------------------
EMAIL_ADDRESS
EMAIL_PASSWORD

EMAIL_PASSWORD should be a Gmail App Password. It is intentionally not
hard-coded in this script.
"""

from __future__ import annotations

import mimetypes
import os
import re
import smtplib
import ssl
import sys
import time
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable, Sequence

# ============================================================================
# SENDER SETTINGS
# ============================================================================

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "er.mdirshad44@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "fjve kcqe edps zfub")  # Use Gmail App Password from environment variable
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SEND_DELAY_SECONDS = 2

# Every email uses this greeting, regardless of recipient address.
RECIPIENT_NAME = "Recruiter"

# ============================================================================
# DAILY ROLE FOLDERS
# ============================================================================

# Process only these known folders, in this exact order.
# Missing folders are skipped automatically.
ROLE_FOLDERS = (
    "aiengineer",
    "dataengineer",
    "pythondeveloper",
)

# ============================================================================
# EMAIL REGEX
# ============================================================================

EMAIL_PATTERN = re.compile(
    r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}",
    re.IGNORECASE,
)

EMAIL_NUMBER_LINE_PATTERN = re.compile(
    r"^\s*(?:[-*]\s*)?# Emails\s*:\s*(.*)$",
    re.IGNORECASE,
)

# ============================================================================
# ROLE CONFIG
# ============================================================================

@dataclass(frozen=True)
class RoleEmailConfig:
    role_name: str
    role_folder: Path
    email_reply_text_path: Path
    jd_text_path: Path
    attachment_path: Path
    recipients: tuple[str, ...]


# ============================================================================
# COMMON FILE HELPERS
# ============================================================================

def _all_files_with_suffix(folder: Path, suffix: str) -> list[Path]:
    """
    Recursively return files with the requested suffix, case-insensitively.

    Using rglob('*') instead of rglob('*.pdf') keeps suffix matching portable
    when files have uppercase extensions such as .PDF.
    """
    wanted = suffix.casefold()

    return sorted(
        (
            path
            for path in folder.rglob("*")
            if path.is_file() and path.suffix.casefold() == wanted
        ),
        key=lambda path: str(path).casefold(),
    )


def _first_non_empty_line(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="replace")

    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped

    return ""


# ============================================================================
# DISCOVER EMAIL REPLY TXT
# ============================================================================

def find_email_reply_text(role_folder: Path) -> Path:
    txt_files = _all_files_with_suffix(role_folder, ".txt")

    if not txt_files:
        raise FileNotFoundError(
            f"No .txt files found in role folder: {role_folder}"
        )

    # Strongest rule: filename contains "email_reply".
    named_candidates = [
        path
        for path in txt_files
        if "email_reply" in path.stem.casefold()
    ]

    # Validate candidate format: first non-empty line must be Subject: ...
    named_valid = [
        path
        for path in named_candidates
        if _first_non_empty_line(path).casefold().startswith("subject:")
    ]

    if len(named_valid) == 1:
        return named_valid[0]

    if len(named_valid) > 1:
        names = "\n".join(f"  - {path}" for path in named_valid)
        raise RuntimeError(
            "More than one email-reply .txt file was found. "
            "Cannot safely choose one:\n"
            f"{names}"
        )

    # Fallback: any non-JD text file whose first non-empty line is Subject:.
    format_candidates = [
        path
        for path in txt_files
        if "email_reply" not in path.stem.casefold()
        and path.name.casefold() != "jd.txt"
        and _first_non_empty_line(path).casefold().startswith("subject:")
    ]

    if len(format_candidates) == 1:
        return format_candidates[0]

    if len(format_candidates) > 1:
        names = "\n".join(f"  - {path}" for path in format_candidates)
        raise RuntimeError(
            "More than one Subject-based email-reply .txt file was found. "
            "Rename the intended file to include 'email_reply':\n"
            f"{names}"
        )

    raise FileNotFoundError(
        "Could not find the email-reply text file in "
        f"{role_folder}. Expected a .txt file containing 'email_reply' "
        "whose first non-empty line starts with 'Subject:'."
    )


# ============================================================================
# DISCOVER JD TXT
# ============================================================================

def find_jd_text(
    role_folder: Path,
    email_reply_text_path: Path,
) -> Path:
    txt_files = [
        path
        for path in _all_files_with_suffix(role_folder, ".txt")
        if path.resolve() != email_reply_text_path.resolve()
    ]

    # Best match: exact jd.txt anywhere inside role folder.
    exact_jd = [
        path for path in txt_files if path.name.casefold() == "jd.txt"
    ]

    if len(exact_jd) == 1:
        return exact_jd[0]

    if len(exact_jd) > 1:
        names = "\n".join(f"  - {path}" for path in exact_jd)
        raise RuntimeError(
            "More than one exact jd.txt file was found:\n"
            f"{names}"
        )

    # Fallback: filename contains "jd", but exclude reply files.
    jd_candidates = [
        path
        for path in txt_files
        if "jd" in path.stem.casefold()
        and "email_reply" not in path.stem.casefold()
        and "reply" not in path.stem.casefold()
    ]

    if len(jd_candidates) == 1:
        return jd_candidates[0]

    if len(jd_candidates) > 1:
        names = "\n".join(f"  - {path}" for path in jd_candidates)
        raise RuntimeError(
            "More than one JD .txt file was found. "
            "Rename the intended source file to exactly 'jd.txt':\n"
            f"{names}"
        )

    raise FileNotFoundError(
        f"Could not find jd.txt in role folder: {role_folder}"
    )


# ============================================================================
# EXTRACT RECIPIENTS FROM "# Emails:"
# ============================================================================

def extract_unique_emails(raw_text: str) -> list[str]:
    emails: list[str] = []
    seen: set[str] = set()

    for match in EMAIL_PATTERN.findall(raw_text or ""):
        email = match.strip()
        key = email.casefold()

        if key in seen:
            continue

        seen.add(key)
        emails.append(email)

    return emails


def extract_recipient_emails_from_jd(jd_path: Path) -> list[str]:
    """
    Extract email addresses ONLY from # Emails: lines.

    Example:
        # Emails: one@example.com, two@example.com, +91...
    """
    text = jd_path.read_text(encoding="utf-8-sig", errors="replace")

    recipients: list[str] = []
    seen: set[str] = set()
    marker_count = 0

    for line in text.splitlines():
        match = EMAIL_NUMBER_LINE_PATTERN.match(line)

        if not match:
            continue

        marker_count += 1
        value_after_marker = match.group(1)

        for email in EMAIL_PATTERN.findall(value_after_marker):
            email = email.strip()
            key = email.casefold()

            if key in seen:
                continue

            seen.add(key)
            recipients.append(email)

    if marker_count == 0:
        print(
            f"⚠️ No '# Emails:' line found in JD file: {jd_path.name}"
        )
    elif not recipients:
        print(
            f"⚠️ '# Emails:' found, but no valid email addresses "
            f"were present in: {jd_path.name}"
        )

    return recipients


# ============================================================================
# DISCOVER CV PDF
# ============================================================================

def find_cv_pdf(role_folder: Path) -> Path:
    pdf_files = _all_files_with_suffix(role_folder, ".pdf")

    if not pdf_files:
        raise FileNotFoundError(
            f"No PDF files found in role folder: {role_folder}"
        )

    cv_candidates = [
        path
        for path in pdf_files
        if "cv" in path.stem.casefold()
    ]

    if len(cv_candidates) == 1:
        return cv_candidates[0]

    if len(cv_candidates) > 1:
        preferred = [
            path
            for path in cv_candidates
            if "md_irshad_cv" in path.stem.casefold()
        ]

        if len(preferred) == 1:
            return preferred[0]

        names = "\n".join(f"  - {path}" for path in cv_candidates)
        raise RuntimeError(
            "More than one PDF filename contains 'cv'. "
            "Cannot safely choose the attachment:\n"
            f"{names}"
        )

    names = "\n".join(f"  - {path}" for path in pdf_files)
    raise FileNotFoundError(
        "PDF files were found, but none has 'cv' in the filename.\n"
        f"Available PDFs:\n{names}"
    )


# ============================================================================
# BUILD ONE ROLE CONFIG AUTOMATICALLY
# ============================================================================

def discover_role_config(
    role_name: str,
    role_folder: Path,
) -> RoleEmailConfig:
    email_reply_path = find_email_reply_text(role_folder)

    jd_path = find_jd_text(
        role_folder=role_folder,
        email_reply_text_path=email_reply_path,
    )

    cv_path = find_cv_pdf(role_folder)

    recipients = extract_recipient_emails_from_jd(jd_path)

    return RoleEmailConfig(
        role_name=role_name,
        role_folder=role_folder,
        email_reply_text_path=email_reply_path,
        jd_text_path=jd_path,
        attachment_path=cv_path,
        recipients=tuple(recipients),
    )


# ============================================================================
# LOAD EMAIL REPLY
# ============================================================================

def load_email_reply(file_path: str | Path) -> tuple[str, str]:
    """
    Read Subject + body from the role's auto-discovered email reply file.
    """
    path = Path(file_path)

    if not path.exists() or not path.is_file():
        raise FileNotFoundError(
            f"Email reply text file not found: {path}"
        )

    text = path.read_text(
        encoding="utf-8-sig",
        errors="replace",
    ).strip()

    if not text:
        raise ValueError(
            f"Email reply text file is empty: {path}"
        )

    lines = text.splitlines()

    first_content_index = next(
        (
            index
            for index, line in enumerate(lines)
            if line.strip()
        ),
        None,
    )

    if first_content_index is None:
        raise ValueError(
            f"Email reply text file is empty: {path}"
        )

    subject_line = lines[first_content_index].strip()

    if not subject_line.casefold().startswith("subject:"):
        raise ValueError(
            "First non-empty line must start with 'Subject:' in "
            f"{path}"
        )

    subject = subject_line.split(":", 1)[1].strip()

    if not subject:
        raise ValueError(
            f"Subject is empty in email reply text file: {path}"
        )

    body = "\n".join(
        lines[first_content_index + 1 :]
    ).strip()

    if not body:
        raise ValueError(
            f"Email body is empty in email reply text file: {path}"
        )

    # Force the first Dear ... greeting to address Recruiter.
    greeting_pattern = re.compile(
        r"^\s*Dear\s+[^,\n]+,\s*$",
        re.IGNORECASE | re.MULTILINE,
    )

    replacement = f"Dear {RECIPIENT_NAME},"

    if greeting_pattern.search(body):
        body = greeting_pattern.sub(
            replacement,
            body,
            count=1,
        )
    else:
        body = f"{replacement}\n\n{body}"

    return subject, body


# ============================================================================
# SETTINGS VALIDATION
# ============================================================================

def validate_sender_settings() -> None:
    if not EMAIL_ADDRESS:
        raise RuntimeError(
            "EMAIL_ADDRESS is missing. Set it as an environment variable."
        )

    if not EMAIL_PASSWORD:
        raise RuntimeError(
            "EMAIL_PASSWORD is missing. Set your Gmail App Password "
            "as an environment variable before running this script."
        )

    if "@" not in EMAIL_ADDRESS:
        raise ValueError(
            f"Invalid EMAIL_ADDRESS: {EMAIL_ADDRESS!r}"
        )


# ============================================================================
# ATTACHMENT
# ============================================================================

def add_attachment_if_exists(
    msg: EmailMessage,
    file_path: str | Path,
) -> bool:
    path = Path(file_path)

    if not path.exists() or not path.is_file():
        print(
            f"⚠️ Attachment skipped. File not found: {path}"
        )
        return False

    mime_type, _ = mimetypes.guess_type(path.name)

    if mime_type:
        main_type, sub_type = mime_type.split("/", 1)
    else:
        main_type, sub_type = (
            "application",
            "octet-stream",
        )

    msg.add_attachment(
        path.read_bytes(),
        maintype=main_type,
        subtype=sub_type,
        filename=path.name,
    )

    return True


# ============================================================================
# BUILD EMAIL
# ============================================================================

def build_message(
    recipient_email: str,
    subject: str,
    body: str,
    attachment_paths: Sequence[str | Path],
) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = recipient_email
    msg.set_content(body)

    for attachment_path in attachment_paths:
        add_attachment_if_exists(
            msg,
            attachment_path,
        )

    return msg


# ============================================================================
# SMTP
# ============================================================================

def open_smtp_connection() -> smtplib.SMTP:
    context = ssl.create_default_context()
    server = smtplib.SMTP(
        SMTP_HOST,
        SMTP_PORT,
        timeout=30,
    )

    try:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(
            EMAIL_ADDRESS,
            EMAIL_PASSWORD,
        )
    except Exception:
        try:
            server.quit()
        except Exception:
            pass

        raise

    return server


# ============================================================================
# SEND ONE ROLE
# ============================================================================

def send_all_emails(
    recipients: Iterable[str],
    subject: str,
    body: str,
    attachment_paths: Sequence[str | Path],
) -> tuple[int, int]:
    recipient_list = list(recipients)

    if not recipient_list:
        print(
            "No valid recipients found. Nothing was sent for this role."
        )
        return 0, 0

    sent_count = 0
    failed_count = 0

    with open_smtp_connection() as server:
        total = len(recipient_list)

        for index, email in enumerate(
            recipient_list,
            start=1,
        ):
            print(
                f"[{index}/{total}] Sending email to: "
                f"{RECIPIENT_NAME} <{email}>"
            )

            try:
                msg = build_message(
                    recipient_email=email,
                    subject=subject,
                    body=body,
                    attachment_paths=attachment_paths,
                )

                # server.send_message(
                #     msg,
                #     from_addr=EMAIL_ADDRESS,
                #     to_addrs=[email],
                # )

                sent_count += 1
                print(
                    f"✅ Email sent successfully to {email}"
                )

            except smtplib.SMTPRecipientsRefused as exc:
                failed_count += 1
                print(
                    f"❌ Recipient refused for {email}: {exc}"
                )

            except smtplib.SMTPException as exc:
                failed_count += 1
                print(
                    f"❌ SMTP error while sending to {email}: {exc}"
                )

            except OSError as exc:
                failed_count += 1
                print(
                    f"❌ File/network error while sending to "
                    f"{email}: {exc}"
                )

            except Exception as exc:
                failed_count += 1
                print(
                    f"❌ Unexpected error while sending to "
                    f"{email}: {exc}"
                )

            if index < total:
                time.sleep(SEND_DELAY_SECONDS)

    return sent_count, failed_count


# ============================================================================
# PROCESS ONE ROLE FOLDER
# ============================================================================

def process_role_folder(
    role_name: str,
    role_folder: Path,
) -> tuple[int, int]:
    print("\n" + "=" * 90)
    print(f"ROLE: {role_name}")
    print(f"Folder: {role_folder}")
    print("=" * 90)

    config = discover_role_config(
        role_name=role_name,
        role_folder=role_folder,
    )

    subject, body = load_email_reply(
        config.email_reply_text_path
    )

    print(
        f"Email reply file : "
        f"{config.email_reply_text_path.name}"
    )
    print(
        f"JD source file   : "
        f"{config.jd_text_path.name}"
    )
    print(
        f"CV attachment    : "
        f"{config.attachment_path.name}"
    )
    print(
        f"Recipients found : "
        f"{len(config.recipients)}"
    )
    print(f"Subject          : {subject}")

    if config.recipients:
        print(
            "Recipients        : "
            + ", ".join(config.recipients)
        )

    return send_all_emails(
        recipients=config.recipients,
        subject=subject,
        body=body,
        attachment_paths=[
            config.attachment_path,
        ],
    )


# ============================================================================
# MAIN DAILY-FOLDER AUTOMATION
# ============================================================================

def main(folder_path: str | Path) -> None:
    r"""
    Process every supported role folder inside one daily folder.

    Example:
        main(
            r"job_profile\specific\company\2026_09_17"
        )
    """
    validate_sender_settings()

    daily_folder = Path(folder_path).expanduser()

    if not daily_folder.exists():
        raise FileNotFoundError(
            f"Daily folder does not exist: {daily_folder}"
        )

    if not daily_folder.is_dir():
        raise NotADirectoryError(
            f"folder_path is not a directory: {daily_folder}"
        )

    print("=" * 90)
    print("AUTOMATED DAILY JOB EMAIL SENDER")
    print(f"Daily folder: {daily_folder.resolve()}")
    print("=" * 90)

    total_sent = 0
    total_failed = 0
    processed_roles = 0
    skipped_missing_roles = 0
    configuration_failed_roles = 0

    for role_name in ROLE_FOLDERS:
        role_folder = daily_folder / role_name

        if not role_folder.exists():
            print(
                f"\n⏭️  Folder not present, skipping: "
                f"{role_name}"
            )
            skipped_missing_roles += 1
            continue

        if not role_folder.is_dir():
            print(
                f"\n⚠️ Expected a folder but found something else, "
                f"skipping: {role_folder}"
            )
            configuration_failed_roles += 1
            continue

        try:
            sent_count, failed_count = process_role_folder(
                role_name=role_name,
                role_folder=role_folder,
            )

            processed_roles += 1
            total_sent += sent_count
            total_failed += failed_count

        except Exception as exc:
            configuration_failed_roles += 1

            print(
                f"\n❌ Could not process role folder: "
                f"{role_name}"
            )
            print(
                f"Reason: {type(exc).__name__}: {exc}"
            )

            # Continue with the next role folder instead of stopping
            # the entire daily run.
            continue

    print("\n" + "=" * 90)
    print("DAILY EMAIL AUTOMATION COMPLETED")
    print(f"Processed role folders : {processed_roles}")
    print(
        f"Missing role folders   : "
        f"{skipped_missing_roles}"
    )
    print(
        f"Role config failures   : "
        f"{configuration_failed_roles}"
    )
    print(f"Emails sent            : {total_sent}")
    print(f"Email send failures    : {total_failed}")
    print("=" * 90)


# ============================================================================
# COMMAND LINE
# ============================================================================

if __name__ == "__main__":
    from datetime import datetime
    today_date = datetime.now().strftime("%Y-%m-%d")
    folder_path = f"job_profile/specific/company/{today_date}"
    
    main(folder_path)
