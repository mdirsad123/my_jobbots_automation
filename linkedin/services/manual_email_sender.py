"""
python -m linkedin.services.manual_email_sender

"""

from __future__ import annotations
import mimetypes
import os
import re
import smtplib
import ssl
import time
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable

# -----------------------------
# Sender settings
# -----------------------------
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "mdirsadtech7305@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "ippq cczp hwkn jyrl")  # Use Gmail App Password from environment variable
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SEND_DELAY_SECONDS = 2


RECIPIENT_NAME = "Recruiter"

# The greeting in the file is automatically replaced with "Dear Recruiter,".
EMAIL_REPLY_TEXT_PATH = (
    r"D:\ird-projects\sahil_projects\my_jobbots_automation\job_profile\specific\company\2026_09_17\pythondeveloper\jd_email_reply_2026_09_17.txt"
)

# -----------------------------
# Attachments
# -----------------------------
# Add PDF/DOCX/etc. paths here. Missing files are skipped with a warning.
ATTACHMENT_PATHS = [
    r"D:\ird-projects\sahil_projects\my_jobbots_automation\job_profile\specific\company\2026_09_17\pythondeveloper\md_irsad_2026_09_17.pdf"
]

# -----------------------------
# Recipient emails
# -----------------------------
RECIPIENT_EMAILS = r"""
bliss.tallentpoint@gmail.com, Nikita.upadhyay@thoughts2binary.com, md.faisal@signinsol.com, jyothirmai@uhvsoftwaresolutions.com, akhila@thesancloud.com, navyaboora@moldite.com, isha@moldite.com, tchauhan@vyzeinc.com, guna@inteliroute.net, keerthana@raad7.com, vivekraj@raad7.com, lokesh@inteliroute.net, pranav@itkeysource.com, b.sairam@3shooltech.com, deepika@inteliroute.net, divyani.parche@kforce.co.in, recruiter4@qween.in, vishakha.jhamnani@kforce.co.in, careers@ssmtb.com, Bhargav@volgotechnologies.com, safasf@inducthr.com, bhanu@intellisofttech.com, hrritu474@gmail.com, hr.ritu072@gmail.com, anwesha.das@intelliest.in, hr@pssoft.co.in, Subhani.p@tekskills.in, sdarshini@virtusa.com, beena.babu@exultglobal.com, prayashkashyap99@gmail.com, gsoumyajit094@gmail.com, sourcing@resoftwa.com, karthik.a@terbiumtech.com, saisanthosh.g@terbiumtech.com, mary_r@trigent.com, sandeep.k@jconnectinc.com, monika.a@tekskills.in, ben@prowesys.com, catherine@infowaygroup.com, hr@quantasis.com, niveditha.m@testunity.com, Nawazish@spruceinfotech.com, monali.santra@enfec.com, ambar@starquesttech.com, madhan.b@astika.in, psobhagya@teksystems.com, sajan.g@martinettechnologies.com, ragamai.j@humacinc.com, shreeraj.thombare@thinkitive.com, anusha.k@saranshinc.com, yatharth.tyagi@wsneconsulting.com, karanlumbhani97@gmail.com, navyaboora@moldite.com, vikram@microstackit.com, rishitha.b@martinettechnologies.com, ilavarapu.pravallika@testunity.com, charandeep.singh@mamsys.com, amit.m@smartitframe.com, nawaz@tekorg.com, Suresh@gracevirtue.com, mansi.naik@lagozon.com, arunprasath82@yahoo.com, viraf.bokdawalla@frontdoor.com, prachi@gudah.co.in, sumakv@optimhire.com, banideepa.barman@dexian.com, hrtrinexglobal@gmail.com, Naveen.kandipalli@shaftsoftwares.com, banika.wazir@programming.com, piyusha.r@apideltech.com, chaitanya.sahaya@qzigma.com, nesanooru.m@esolglobal.com, gokila27396@gmail.com, mohit.goyal@talentxo.in, PBalasubramaniyam@datamaxis.net, Keerti@infowaygroup.com, suman.g@alchemytechsol.com, Snehas@vbeyond.com, Muskan@raspitsolutions.com, priyadarshini.u@martinettechnologies.com, sriram.g@manvision.net, nishi.panchal@digitrixsoftware.com, khushboo.sehgal@rarrtech.com, himadree@drcsystems.com, Danish@metrixit.com, paul@ventechsoft.com, aaradhya@jpitstaffing.com, dhanakrajput1011@gmail.com, manju@callistotalentsolutions.com, shivani@excelonsolutions.com, nazia@n2psystems.ca, srutee.mishra@5exceptions.com, sukesh@lovasit.com, rosyvijay1611@gmail.com, Tanyakharb47@gmail.com, Sandeep@aimplusstaffing.com, PJ@Siriuslync.com, Pj.itrecruiter@gmail.com, recruitment@neevsystems.com, ayushgarg@Thoucentric.com, p.priyanka@shrasits.com, deepika.sahu@teamlease.com, venu.c@vrntech.us, manpreet.kaur@talentpotentialconsulting.in, swadhii@bloomsolutions.com, arpit@hexgs.com
"""

EMAIL_PATTERN = re.compile(
    r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}",
    re.IGNORECASE,
)

def extract_recipient_emails(raw_text: str) -> list[str]:
    """Extract unique email addresses from plain text or Markdown mailto links."""
    emails: list[str] = []
    seen: set[str] = set()

    for match in EMAIL_PATTERN.findall(raw_text):
        email = match.strip()
        key = email.casefold()
        if key in seen:
            continue
        seen.add(key)
        emails.append(email)

    return emails

def load_email_reply(file_path: str | Path) -> tuple[str, str]:
    """Read subject and body from the email-reply text file."""
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Email reply text file not found: {path}")

    text = path.read_text(encoding="utf-8-sig").strip()
    if not text:
        raise ValueError(f"Email reply text file is empty: {path}")

    lines = text.splitlines()

    # Ignore leading blank lines, then require a Subject: line.
    first_content_index = next(
        (index for index, line in enumerate(lines) if line.strip()),
        None,
    )
    if first_content_index is None:
        raise ValueError(f"Email reply text file is empty: {path}")

    subject_line = lines[first_content_index].strip()
    if not subject_line.lower().startswith("subject:"):
        raise ValueError(
            f"First non-empty line must start with 'Subject:' in {path}"
        )

    subject = subject_line.split(":", 1)[1].strip()
    if not subject:
        raise ValueError(f"Subject is empty in email reply text file: {path}")

    body = "\n".join(lines[first_content_index + 1 :]).strip()
    if not body:
        raise ValueError(f"Email body is empty in email reply text file: {path}")

    # Force the first Dear ... greeting to always address the recipient as Recruiter.
    greeting_pattern = re.compile(r"^\s*Dear\s+[^,\n]+,\s*$", re.IGNORECASE | re.MULTILINE)
    replacement = f"Dear {RECIPIENT_NAME},"

    if greeting_pattern.search(body):
        body = greeting_pattern.sub(replacement, body, count=1)
    else:
        body = f"{replacement}\n\n{body}"

    return subject, body

def validate_settings() -> None:
    """Fail early when required sender settings are missing."""
    if not EMAIL_ADDRESS:
        raise RuntimeError(
            "EMAIL_ADDRESS is missing. Set it as an environment variable."
        )

    if not EMAIL_PASSWORD:
        raise RuntimeError(
            "EMAIL_PASSWORD is missing. Set your Gmail App Password as an "
            "environment variable before running this script."
        )

    if "@" not in EMAIL_ADDRESS:
        raise ValueError(f"Invalid EMAIL_ADDRESS: {EMAIL_ADDRESS!r}")

def add_attachment_if_exists(msg: EmailMessage, file_path: str) -> bool:
    """Attach one file when it exists; return whether it was attached."""
    path = Path(file_path)

    if not path.exists() or not path.is_file():
        print(f"⚠️ Attachment skipped. File not found: {path}")
        return False

    mime_type, _ = mimetypes.guess_type(path.name)
    if mime_type:
        main_type, sub_type = mime_type.split("/", 1)
    else:
        main_type, sub_type = "application", "octet-stream"

    msg.add_attachment(
        path.read_bytes(),
        maintype=main_type,
        subtype=sub_type,
        filename=path.name,
    )
    return True

def build_message(
    recipient_email: str,
    subject: str,
    body: str,
) -> EmailMessage:
    """Create one private email for one recipient."""
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = recipient_email
    msg.set_content(body)

    for attachment_path in ATTACHMENT_PATHS:
        add_attachment_if_exists(msg, attachment_path)

    return msg

def open_smtp_connection() -> smtplib.SMTP:
    """Open and authenticate one reusable TLS SMTP connection."""
    context = ssl.create_default_context()
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)

    try:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    except Exception:
        try:
            server.quit()
        except Exception:
            pass
        raise

    return server

def send_all_emails(
    recipients: Iterable[str],
    subject: str,
    body: str,
) -> tuple[int, int]:
    """Send one separate email per recipient and return success/failure counts."""
    recipient_list = list(recipients)
    if not recipient_list:
        print("No valid recipients found. Nothing was sent.")
        return 0, 0

    sent_count = 0
    failed_count = 0

    with open_smtp_connection() as server:
        total = len(recipient_list)

        for index, email in enumerate(recipient_list, start=1):
            print(
                f"[{index}/{total}] Sending email to: "
                f"{RECIPIENT_NAME} <{email}>"
            )

            try:
                msg = build_message(email, subject, body)
                server.send_message(
                    msg,
                    from_addr=EMAIL_ADDRESS,
                    to_addrs=[email],
                )
                sent_count += 1
                print(f"✅ Email sent successfully to {email}")
            except smtplib.SMTPRecipientsRefused as exc:
                failed_count += 1
                print(f"❌ Recipient refused for {email}: {exc}")
            except smtplib.SMTPException as exc:
                failed_count += 1
                print(f"❌ SMTP error while sending to {email}: {exc}")
            except OSError as exc:
                failed_count += 1
                print(f"❌ File/network error while sending to {email}: {exc}")
            except Exception as exc:
                failed_count += 1
                print(f"❌ Unexpected error while sending to {email}: {exc}")

            if index < total:
                time.sleep(SEND_DELAY_SECONDS)

    return sent_count, failed_count

def main() -> None:
    validate_settings()

    subject, body = load_email_reply(EMAIL_REPLY_TEXT_PATH)
    recipients = extract_recipient_emails(RECIPIENT_EMAILS)

    print(f"Email reply file: {EMAIL_REPLY_TEXT_PATH}")
    print(f"Subject: {subject}")
    print(f"Recipients found: {len(recipients)}")

    sent_count, failed_count = send_all_emails(
        recipients=recipients,
        subject=subject,
        body=body,
    )

    print("\nEmail sending completed.")
    print(f"Successful: {sent_count}")
    print(f"Failed:     {failed_count}")

if __name__ == "__main__":
    main()
