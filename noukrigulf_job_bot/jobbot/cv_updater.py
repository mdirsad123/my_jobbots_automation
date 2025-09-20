"""
python linkedin_job_bot/jobbot/cv_updater.py
python -m linkedin_job_bot.jobbot.cv_updater
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
    #     compressed_path = pdf_path.replace(".pdf", "_compress.pdf")
    #     compressed_pdf = compress_pdf(pdf_path, compressed_path)
    #     print(f"Compressed PDF saved at: {compressed_pdf}")
    #     return compressed_pdf
    # except Exception as e:
    #     print(f"Failed to convert to PDF: {e}")
    #     return output_path  # fallback to docx


# ----------- Sample Usage ----------- #

if __name__ == '__main__':
    current_dir = os.path.dirname(__file__)
    docx_file   = os.path.join(current_dir, "Md_Irsad_ind.docx")
    output_file = os.path.join(current_dir, "updated_resume.docx")

    updated_roles = {
    "Project #1 – Insights Content": {
        "point1": "Designed and developed secure, scalable AWS API integrations using API Gateway, Lambda (Python), and Step Functions, ensuring seamless data exchange across systems.",
        "point2": "Implemented and optimized ETL workflows with Airflow, enhancing data processing efficiency and reliability in cross-functional projects.",
        "point3": "Applied RESTful APIs, and JSON/XML to build robust, high-performance integrations aligned with AWS security best practices.",
        "point4": "Collaborated with DevOps teams to integrate version control and CI/CD pipelines, ensuring streamlined deployment and maintenance of microservices and database (RDS/DynamoDB) interactions.",
    },
    "Project #2 – MQR": {
        "point1": "Designed and implemented secure, scalable AWS API integrations using API Gateway, Lambda (Python), and Step Functions, ensuring high performance and reliability across multiple systems.",
        "point2": "Developed and optimized data workflows with Airflow, enhancing efficiency in data exchange processes while adhering to RESTful API standards.",
        "point3": "Collaborated with cross-functional teams to gather requirements and deliver robust solutions, leveraging JSON/XML and Python scripting for seamless integration.",
        "point4": "Applied security best practices and DevOps methodologies, including version control and CI/CD pipelines, to maintain and deploy integrations in a microservices architecture with RDS and DynamoDB.",
    },
    "PROJECT #2 – DATA CONTENT": {
        "point1": "Designed and developed secure, scalable AWS API integrations using API Gateway, Lambda (Python), and Step Functions, ensuring seamless data exchange across systems.",
        "point2": "Implemented and optimized data workflows with Airflow, enhancing integration reliability and performance for cross-functional teams.",
        "point3": "Applied RESTful APIs, and JSON/XML to build robust, secure, and efficient data interfaces aligned with AWS security best practices.",
        "point4": "Collaborated with DevOps teams to integrate version control and CI/CD pipelines, leveraging microservices and databases (RDS, DynamoDB) for streamlined deployments.",
    },
    "Summary": "Senior Software Engineer with 9.5 years of experience, specializing in AWS cloud technologies including IAM, S3, EC2, Athena, Glue, Step Functions, and CloudWatch. Proficient in designing ETL pipelines using Python, Pandas, PySpark, and SQL, with expertise in machine learning algorithms (classification, regression, random forest). Skilled in performance optimization through caching, code reviews with SonarLint/SonarQube, and project setup using Conda and Poetry. Experienced in RESTful APIs, JSON/XML, and Python scripting, with a strong foundation in secure and efficient data integration practices. Familiar with DevOps tools, version control, CI/CD pipelines, and microservices architectures, including RDS and DynamoDB. AWS certified."}



    # update_roles_in_docx(docx_file, updated_roles, output_file)
    # print("✅ Done. Updated resume saved to:", output_file)

    input_pdf_path = r"D:\ird-projects\my_pyautomation\noukrigulf_job_bot\output\Md_Irsad_vaporvm.pdf"

    compress_pdf(input_pdf_path, input_pdf_path.replace(".pdf", "_cv.pdf"))
