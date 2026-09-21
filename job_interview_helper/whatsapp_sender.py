"""
python email_sender.py

Bulk-but-personal outreach email sender for AlgoAgentX portfolio.

How to run:
1) Set your Gmail app password as an environment variable:
   Windows PowerShell:
     $env:EMAIL_PASSWORD="your_gmail_app_password"
   macOS/Linux:
     export EMAIL_PASSWORD="your_gmail_app_password"

2) Update DEMO_VIDEO_URL, CASE_STUDY_URL, RESUME_URL if you want link-based sharing.
3) Keep RESUME_PDF_PATH if you also want to attach the resume PDF.
4) Run:
   python email_sender_updated.py

Important: Send only to people/teams where outreach is relevant. Keep the list small and personalized.
"""

import os
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from pathlib import Path

# -----------------------------
# Sender settings
# -----------------------------
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "mdirsadtech7305@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "ippq cczp hwkn jyrl")  # Use Gmail App Password from environment variable
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

# -----------------------------
# Portfolio links - replace these with your public links
# -----------------------------
DEMO_VIDEO_URL = "https://drive.google.com/file/d/1d0fRScmf5avkbfaqDSVfURf93LufGZJB/view?usp=sharing"
CASE_STUDY_URL = "https://drive.google.com/file/d/1sIPNVAfdtKb_LWviS4Pa5l5Tlr7XrkOo/view?usp=sharing"
RESUME_URL = "https://drive.google.com/file/d/1k3suHwOiWjX0VYS2O4_OIKuJc4u9cC7f/view?usp=sharing"  # Optional if you also attach resume

# Optional resume attachment path. Keep empty string "" if you only want link-based sharing.
RESUME_PDF_PATH = "Md_Irsad.pdf"

SUBJECT = "AlgoAgentX Demo — Algorithmic Trading SaaS & Python Development"

def build_plain_body(recipient_name: str) -> str:
    return f"""
<html>
  <body style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #111;">
    <p>Hi {recipient_name},</p>

    <p>I’ve been following your work in trading and really appreciate the value you bring to the trading community.</p>

    <p>
      I wanted to reach out because I’m a <b>Python Backend Engineer</b> with hands-on experience in
      <b>algorithmic trading systems, backtesting, broker integration, and trading automation</b>.
    </p>

    <p>
      I have recently built an algorithmic trading SaaS project called <b>AlgoAgentX</b> as my proof-of-work project.
      I’m looking for an opportunity to contribute to a serious trading team, trader community, or fintech/trading product
      where I can support Python development, backtesting tools, automation workflows, broker integrations,
      or strategy execution systems.
    </p>

    <p>
      I would be grateful if you could review my work and consider me for any suitable opportunity to work or collaborate with you.
    </p>

    <p>
      <b>Demo Video:</b> <a href="{DEMO_VIDEO_URL}">View Demo Video</a><br>
      <b>Case Study PDF:</b> <a href="{CASE_STUDY_URL}">View Case Study</a><br>
      <b>Resume:</b> <a href="{RESUME_URL}">View Resume</a>
    </p>

    <p>Thank you for your time. I look forward to hearing from you.</p>

    <p>
      Best regards,<br>
      <b>Md Irsad</b><br>
      Python Backend Engineer | Algo Trading Systems | FinTech SaaS<br>
      +91 8409718735<br>
      <a href="mailto:mdirsadtech7305@gmail.com">mdirsadtech7305@gmail.com</a>
    </p>
  </body>
</html>
"""

def build_html_body(recipient_name: str) -> str:
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #111;">
        <p>Hi {recipient_name},</p>

        <p>I’ve been following your work in trading and really appreciate the value you bring to the trading community.</p>

        <p>
        I wanted to reach out because I’m a <b>Python Backend Engineer</b> with hands-on experience in
        <b>algorithmic trading systems, backtesting, broker integration, and trading automation</b>.
        </p>

        <p>
        I have recently built an algorithmic trading SaaS project called <b>AlgoAgentX</b> as my proof-of-work project.
        I’m looking for an opportunity to contribute to a serious trading team, trader community, or fintech/trading product
        where I can support Python development, backtesting tools, automation workflows, broker integrations,
        or strategy execution systems.
        </p>

        <p>
        I would be grateful if you could review my work and consider me for any suitable opportunity to work or collaborate with you.
        </p>

        <p>
        <b>Demo Video:</b> <a href="{DEMO_VIDEO_URL}">View Demo Video</a><br>
        <b>Case Study PDF:</b> <a href="{CASE_STUDY_URL}">View Case Study</a><br>
        <b>Resume:</b> <a href="{RESUME_URL}">View Resume</a>
        </p>

        <p>Thank you for your time. I look forward to hearing from you.</p>

        <p>
        Best regards,<br>
        <b>Md Irsad</b><br>
        Python Backend Engineer | Algo Trading Systems | FinTech SaaS<br>
        +91 8409718735<br>
        <a href="mailto:mdirsadtech7305@gmail.com">mdirsadtech7305@gmail.com</a>
        </p>
    </body>
    </html>
    """

def attach_pdf_if_exists(msg: MIMEMultipart, pdf_path: str) -> None:
    if not pdf_path:
        return

    path = Path(pdf_path)
    if not path.exists():
        print(f"⚠️ Attachment skipped. File not found: {pdf_path}")
        return

    with path.open("rb") as f:
        part = MIMEApplication(f.read(), _subtype="pdf")
        part.add_header("Content-Disposition", "attachment", filename=path.name)
        msg.attach(part)

def send_portfolio_email(recipient_name: str, recipient_email: str, resume_pdf_path: str = RESUME_PDF_PATH) -> None:
    if not EMAIL_PASSWORD:
        raise RuntimeError("EMAIL_PASSWORD is missing. Set it as an environment variable before running.")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = SUBJECT
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = recipient_email

    plain_body = build_plain_body(recipient_name)
    html_body = build_html_body(recipient_name)

    # msg.attach(MIMEText(plain_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    # To attach resume PDF, convert to mixed after attaching alternative parts.
    # Simple approach: attach directly; Gmail accepts it.
    attach_pdf_if_exists(msg, resume_pdf_path)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)


def main() -> None:
    recipients = {
        # Replace/add only relevant contacts.
        # "test irsad": "mdirsa688@gmail.com",
        "Trader Gupta": "9211395372, 9818377737, 8287031379",
    }

    # Safety check before sending.
    if "PASTE_YOUR" in DEMO_VIDEO_URL or "PASTE_YOUR" in CASE_STUDY_URL:
        raise RuntimeError("Please update DEMO_VIDEO_URL and CASE_STUDY_URL before sending emails.")

    for name, email in recipients.items():
        send_portfolio_email(name, email)
        print(f"✅ Email sent to {name} at {email}")
        time.sleep(20)  # Keep a safe delay between emails.

if __name__ == "__main__":
    main()
