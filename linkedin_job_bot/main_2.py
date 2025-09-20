"""
python linkedin_job_bot/main_2.py
python -m linkedin_job_bot.main_2

note: This script is designed to update a CV based on a job description.
"""

import os
from jobbot.summarizer_generate_point import generate_cv_roles
from jobbot.cv_updater import update_roles_in_docx
import sys
from utils.debbuger_port_driver import get_driver
import importlib.util
from jobbot.post_applier import apply_to_job

description = """We are looking for a Data Scientist in Dubai, UAE. if you are interested, please share your updated profile along with the below mentioned 
required details. Minimum 10+ years in AI/ML or data science, with at least 5 years in a leadership role.
Proven experience in banking or financial services is highly preferred.
Hands-on with AI/ML frameworks (e.g., TensorFlow, PyTorch, Scikit-learn) and tools (Python, SQL, Spark).
Experience in Azure ML tools: Databricks etc.
Experience with end-to-end model lifecycle management and MLOps."""

def resume_update():
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    docx_file = "linkedin_job_bot/input/Md_Irsad_ind.docx"
    output_file = os.path.join(output_dir, f"Md_Irsad_cv.docx")
    
    result = generate_cv_roles(description, docx_file)
    
    # Dynamically import fresh updated_roles from generated file
    roles_path = os.path.join(os.path.dirname(__file__), "output", "generated_roles.py")
    spec = importlib.util.spec_from_file_location("generated_roles", roles_path)
    updated_roles_module = importlib.util.module_from_spec(spec)
    sys.modules["generated_roles"] = updated_roles_module
    spec.loader.exec_module(updated_roles_module)
    updated_roles = updated_roles_module.updated_roles

    # Update CV
    update_roles_in_docx(docx_file, updated_roles, output_file)
    print(f"Saved CV -To- {output_file}")
    
    if "Summary" in updated_roles:
        new_summary = updated_roles["Summary"]
        
    # send updated CV via WhatsApp
    driver = get_driver()
    number = "+918409718735"
    message_lines = [
            "Dear Recruiter,",
            "Please find my profile summary and details below,",
            "",
            "Professional Summary:",
            f"{new_summary}",
            "",
            "Total Experience: 2 years",
            "Current Location: Mumbai",
            "Preferred Location: Bangalore/Pune/Noida",
            "Notice Period: 1 month",
            "Serving Notice Period: No",
            "",
            "Looking forward to hearing from you.",
            "",
            "Thanks & Regards,",
            "Irsad",
            "Whatsapp: +91-8409718735"
        ]
    
    # driver.get("https://web.whatsapp.com/")
    # send_workday_job_message(driver, number, message_lines, output_file)
    
    # send updated cv to email
    post_email = "mdirsadtech7305@gmail.com"
    apply_to_job(post_email, new_summary, output_file)
    print(f'Email sent successfully to {post_email}')
    
if __name__ == "__main__":
    resume_update()
