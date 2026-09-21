# linkedin_job_bot/jobbot/job_applier.py

import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jobbot.config import settings  # Import the settings dictionary
from email.mime.application import MIMEApplication

def apply_to_job(recipient_email: str, summary: str, cv_path: str, title: str):
    # build the message container
    msg = MIMEMultipart()
    msg['Subject'] = f'Application for {title} role'
    msg['From'] = settings["EMAIL_ADDRESS"]
    msg['To'] = recipient_email
    # msg['To'] = "mdirsa688@gmail.com"

    # body text with static template and dynamic professional summary
    body = f"""Dear Recruiter,
Please find my profile summary and details below,

Professional Summary:
{summary}

Total Experience: 2+ years
Current Location: Mumbai
Preferred Location: Bangalore/Mumbai/Noida
Notice Period: 1 week
Serving Notice Period: Yes

Looking forward to hearing from you.

Thanks & Regards,
Irsad
Whatsapp:+91-8409718735
"""
    msg.attach(MIMEText(body, 'plain'))

    # attach the CV file
    filename = os.path.basename(cv_path)
    with open(cv_path, 'rb') as f:
        part = MIMEApplication(f.read(), _subtype='pdf')
        part.add_header('Content-Disposition', 'attachment', filename=filename)
    msg.attach(part)

    # send it
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(settings["EMAIL_ADDRESS"], settings["EMAIL_PASSWORD"])
        server.send_message(msg)
