"""
python noukri_dot_com_job_bot/jobbot/cv_updater.py
python -m noukri_dot_com_job_bot.jobbot.cv_updater
"""

import os
import sys
import time
from PIL import Image
import io
from docx2pdf import convert
from docx import Document
from docx.shared import Pt
import fitz

def compress_pdf(input_path: str, output_path: str, quality: int = 50) -> str:
    """
    Compress a PDF by reducing embedded image quality and removing metadata.
    
    Parameters:
    - input_path: Path to original PDF
    - output_path: Path to save compressed PDF
    - quality: JPEG compression quality (0-100), lower means more compression
    
    Returns:
    - output_path of compressed PDF
    """
    try:
        doc = fitz.open(input_path)
        for page_index in range(len(doc)):
            page = doc[page_index]
            img_list = page.get_images(full=True)
            
            for img_index, img in enumerate(img_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]

                if image_ext.lower() not in ["jpeg", "jpg", "png"]:
                    continue  # skip unsupported formats

                # Convert image to PIL
                image = Image.open(io.BytesIO(image_bytes))
                img_io = io.BytesIO()
                image.save(img_io, format='JPEG', quality=quality)
                new_image_bytes = img_io.getvalue()

                # Replace image in PDF
                new_xref = doc._add_image(new_image_bytes)
                page.replace_image(xref, new_xref)

        doc.save(output_path, garbage=4, deflate=True, clean=True)
        doc.close()
        return output_path

    except Exception as e:
        print(f"Failed to compress PDF: {e}")
        return input_path    

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
    # try:
    #     convert(output_path)
    #     pdf_path = output_path.replace(".docx", ".pdf")
    #     # compressed_path = pdf_path.replace(".pdf", "_compress.pdf")
    #     # compressed_pdf = compress_pdf(pdf_path, compressed_path)
    #     print(f"Compressed PDF saved at: {pdf_path}")
    #     return pdf_path
    # except Exception as e:
    #     print(f"Failed to convert to PDF: {e}")
    #     return output_path  # fallback to docx


# ----------- Sample Usage ----------- #

if __name__ == '__main__':
    current_dir = os.path.dirname(__file__)
    docx_file   = os.path.join("noukri_dot_com_job_bot", "input", "Md_Irsad_ind.docx")
    output_file = os.path.join(current_dir, "updated_resume.docx")

    updated_roles = {
        "Project #1 – Subscription Milestone": {
            "point1": "Installed Python packages via pip, poetry and virtual environments.",
            "point2": "Created command-line tools using Python and argparse.",
            "point3": "Design ETL pipelines with RDS as source or target system.",
            "point4": "Monitor slow queries and optimize indexes using RDS logs.",
            "point5": "Design and train neural networks for various tasks using TensorFlow.",
        },
        "[DYNAMIC TECHNOLOGIES LIST 1]": "data, etl, python, devops, ml, pandas, ai, data science, aws, orm",
        "Project #2 – Insights Content": {
            "point1": "Customize color palettes and themes for better visuals using seaborn.",
            "point2": "Integrate models into admin, views, and serializers using Django ORM.",
            "point3": "Write complex queries using QuerySet chaining using Django ORM.",
            "point4": "Audit key login history and session rules in SSO tools.",
            "point5": "Improve key security and login experience via SSO.",
        },
        "[DYNAMIC TECHNOLOGIES LIST 2]": "data, etl, python, devops, ml, pandas, ai, data science, aws, orm",
        "Project #3 – JazzTrack Management System": {
            "point1": "Remove outliers and errors in data using Python cleaning.",
            "point2": "Use Pandas for handling missing data during cleaning.",
            "point3": "Apply data transformations using Python for modeling.",
            "point4": "Encode, scale, or bin data in transformation workflows.",
            "point5": "Automate feature creation in AI pipelines efficiently.",
        },
        "[DYNAMIC TECHNOLOGIES LIST 3]": "data, etl, python, devops, ml, pandas, ai, data science, aws, orm",
        "Summary": "Full Stack Developer & Data Engineer with 2+ years of experience, specializing in React.js, Python, and AWS cloud technologies including IAM, S3, EC2, Athena, Glue, Step Functions, and CloudWatch. Proficient in designing ETL pipelines using Python, Pandas, PySpark, and SQL for efficient data processing. Skilled in developing machine learning models, including classification, regression, and random forest algorithms. Expertise in performance optimization through caching strategies and adherence to best practices via code reviews with SonarLint/SonarQube, alongside streamlined project management using Conda and Poetry.",
    }



    update_roles_in_docx(docx_file, updated_roles, output_file)
    print("✅ Done. Updated resume saved to:", output_file)
