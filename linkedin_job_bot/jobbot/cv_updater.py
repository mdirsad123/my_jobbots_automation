"""
python linkedin_job_bot/jobbot/cv_updater.py
python -m linkedin_job_bot.jobbot.cv_updater
"""

import os
import sys
import time
from docx2pdf import convert
from docx import Document
from docx.shared import Pt
import fitz

def compress_pdf(input_path: str, output_path: str, quality: int = 50) -> str:
    """
    Compress PDF by reducing image quality and removing metadata.
    """
    try:
        doc = fitz.open(input_path)
        for page in doc:
            # Reduce image quality
            images = page.get_images(full=True)
            for img in images:
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]

                # Reinsert image with reduced quality
                pix = fitz.Pixmap(fitz.csRGB, fitz.Pixmap(image_bytes))
                if pix.n > 3:  # convert to RGB
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                page.insert_image(page.rect, pixmap=pix, overlay=True)

        # Save compressed PDF
        doc.save(output_path, garbage=4, deflate=True, clean=True)
        doc.close()
        return output_path
    except Exception as e:
        print(f"Failed to compress PDF: {e}")
        return input_path  # fallback
    
def update_roles_in_docx(docx_path, updated_roles_dict, output_path):
    doc = Document(docx_path)

    # --- Step 1: Update Project Roles ---
    for i, para in enumerate(doc.paragraphs):
        for project, new_roles in updated_roles_dict.items():
            if project in para.text and isinstance(new_roles, dict):
                print(f"Updating section for: {project} (at index {i})")

                # Find the 'Roles and responsibilities' header
                for j in range(i, len(doc.paragraphs)):
                    if 'Roles and responsibilities' in doc.paragraphs[j].text:
                        insert_idx = j + 1
                        for key, text in new_roles.items():
                            print(f"Writing {project} {key} at paragraph index {insert_idx}")
                            if insert_idx < len(doc.paragraphs):
                                para_to_edit = doc.paragraphs[insert_idx]
                                para_to_edit.text = text
                            else:
                                para_to_edit = doc.add_paragraph(text)

                            # Font formatting
                            for run in para_to_edit.runs:
                                run.font.name = "Arial Nova Cond"
                                run.font.size = Pt(9)

                            insert_idx += 1
                        break  # Done with this project’s block

    # --- Step 2: Update "Professional Summary" ---
    if "Summary" in updated_roles_dict:
        new_summary = updated_roles_dict["Summary"]
        print("Updating 'Professional Summary' section.")

        for i, para in enumerate(doc.paragraphs):
            if "Professional Summary" in para.text:
                summary_index = i + 1
                if summary_index < len(doc.paragraphs):
                    summary_para = doc.paragraphs[summary_index]
                    summary_para.text = new_summary
                else:
                    summary_para = doc.add_paragraph(new_summary)

                for run in summary_para.runs:
                    run.font.name = "Arial Nova Cond"
                    run.font.size = Pt(9)

                print(f"Professional Summary updated at index {summary_index}")
                break
        else:
            print("'Professional Summary' section not found in the document.")

    # --- Save Output ---,
    doc.save(output_path)
    print(f"Updated pdf saved at: {output_path}")
    # Convert to PDF
    try:
        convert(output_path)
        pdf_path = output_path.replace(".docx", ".pdf")
        # compressed_path = pdf_path.replace(".pdf", "_compressed.pdf")
        compressed_pdf = compress_pdf(pdf_path, pdf_path)
        print(f"Compressed PDF saved at: {compressed_pdf}")
        return compressed_pdf
    except Exception as e:
        print(f"Failed to convert to PDF: {e}")
        return output_path  # fallback to docx


# ----------- Sample Usage ----------- #

if __name__ == '__main__':
    current_dir = os.path.dirname(__file__)
    # docx_file   = os.path.join(current_dir, "Md_Irsad_ind.docx")
    docx_file = "linkedin_job_bot/input/Md_Irsad_ind.docx"
    output_file = os.path.join(current_dir, "updated_resume.docx")


    updated_roles = {
        "Project #1 – PrintSoft Replacement": {
            "point1": "Applied Python loops and conditions for data processing.",
            "point2": "Exeption handling in Python using try-except-finally blocks.",
            "point3": "Secure RDS access using IAM roles, VPC, and encryption.",
            "point4": "Monitor slow queries and optimize indexes using RDS logs.",
            "point5": "Deploy models with TensorFlow Serving and TensorFlow Lite using TensorFlow.",
        },
        "[DYNAMIC TECHNOLOGIES LIST 1]": "orm, aws, data science, ai, etl, devops, ml, pandas, data, python",
        "Project #2 – Prod Finance Data Pipeline": {
            "point1": "Integrate with pandas DataFrames for quick plotting using seaborn.",
            "point2": "Handle database schema changes with migrations using Django ORM.",
            "point3": "Perform CRUD operations with Django models using Django ORM.",
            "point4": "Use key IdPs like Azure AD or Okta for SSO setup.",
            "point5": "Improve key security and login experience via SSO.",
        },
        "[DYNAMIC TECHNOLOGIES LIST 2]": "orm, aws, data science, ai, etl, devops, ml, pandas, data, python",
        "Project #3 – JazzTrack Management System": {
            "point1": "Remove outliers and errors in data using Python cleaning.",
            "point2": "Use Pandas for handling missing data during cleaning.",
            "point3": "Prepare model input with smart transformation logic.",
            "point4": "Aggregate values for insights during transformation step.",
            "point5": "Automate feature creation in AI pipelines efficiently.",
        },
        "[DYNAMIC TECHNOLOGIES LIST 3]": "orm, aws, data science, ai, etl, devops, ml, pandas, data, python",
        "Summary": "Data Engineer and Python Developer with 2+ years of experience in designing scalable ETL pipelines, backend APIs, and automation workflows. Proficient in AWS (Glue, Lambda, Step Functions, S3, Redshift), SQL/MySQL, and Python (Pandas, PySpark, FastAPI). Demonstrated success in automating finance workflows, migrating legacy systems to cloud-native solutions, and optimizing database performance. Experienced in both freelancing and full-time roles, delivering measurable business impact through reduced manual effort and enhanced data processing efficiency. Holds a strong foundation in data preprocessing, algorithm implementation, and practical application of data science tools, with a proven ability to teach and mentor in technical environments.",
    }

    update_roles_in_docx(docx_file, updated_roles, output_file)
    # print("✅ Done. Updated resume saved to:", output_file)
