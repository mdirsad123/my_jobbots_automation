"""
python linkedin_job_bot/jobbot/get_roles_responsibility_point.py
python -m linkedin_job_bot.jobbot.get_roles_responsibility_point
"""

import cohere
import re
from pathlib import Path
from docx import Document
import os
import sys
from transformers import pipeline
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
import random  # Make sure this is imported at the top
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from linkedin_job_bot.jobbot.config import settings
from utils.technology_resole_resp import tech_roles_responsibilities
# from linkedin_job_bot.jobbot.four_matcher import compute_semantic_similarity_from_list
import importlib.util

co = cohere.Client(settings["COHERE_API_KEY2"])

PROJECTS = [
    "Project #1 – Subscription Milestone",
    "Project #2 – Insights Content",
    "Project #3 – JazzTrack Management System"
]

def extract_professional_summary(docx_path: str) -> str:
    doc = Document(docx_path)
    for i, para in enumerate(doc.paragraphs):
        if "Professional Summary" in para.text:
            summary_index = i + 1
            if summary_index < len(doc.paragraphs):
                return doc.paragraphs[summary_index].text.strip()
    return ""

def extract_professional_summary(docx_path: str) -> str:
    # print(f"Reading CV from: {docx_path}")
    doc = Document(docx_path)

    for i, para in enumerate(doc.paragraphs):
        if "Professional Summary" in para.text:
            # print(f"Found 'Professional Summary' at index {i}")
            summary_index = i + 1
            if summary_index < len(doc.paragraphs):
                return doc.paragraphs[summary_index].text.strip()
            else:
                raise ValueError("No content found under 'Professional Summary'.")
    raise ValueError("'Professional Summary' section not found in the CV.")

def merge_summary_with_job(existing_summary: str, job_description: str) -> str:
    print("Calling Cohere to merge existing summary with job description")
    response = co.chat(
        message=(
            f"I have this existing professional summary:\n\n{existing_summary}\n\n"
            f"And this is a job summary:\n\n{job_description}\n\n"
            f"Now rewrite only the professional summary as a single clean paragraph. "
            f"Avoid any explanation or introduction. Just the summary in a technical, concise CV tone."
        ),
        temperature=0.4,
        max_tokens=300
    )
    return response.text.strip()

def generate_cv_roles(description: str, docx_path: str) -> str:
    words = description.split()
    lowercase_words = [word.lower() for word in words]

    # Join the words back into a string (optional)
    lowercase_description = ' '.join(lowercase_words)
    
    updated_roles: dict[str, dict[str, str] | str] = {}
    
    tech_roles = {
        key.lower(): value for key, value in tech_roles_responsibilities.items()
    }
    
    # Step 3: Match JD keywords against 'subset' field in tech_roles
    matched_techs = []
    all_subsets = []
    for tech_key, tech_value in tech_roles.items():
        tech_key_lower = tech_key.lower()
        if tech_key_lower in lowercase_description:
            all_subsets.append(tech_roles[tech_key_lower].get("subset", ""))
            matched_techs.append(tech_key_lower)

    # print(f"matched_techs: {matched_techs}")
    all_subsets_lower = [subset.lower() for subset in all_subsets]
    unique_subsets = list(set(all_subsets_lower))
    # print(f"unique_subsets: {unique_subsets}")
    # Step 4: Get bullet points
    all_bullets = []
    for tech in matched_techs:
        bullets = tech_roles.get(tech, {}).get("bullet_points", [])
        if len(bullets) >= 2:
            selected = random.sample(bullets, 2)
        else:
            selected = bullets  # If less than 2, take all
        all_bullets.extend(selected)

    # Step 5: Distribute bullet points across projects with 50% to Project #3 if >= 10 bullets
    bullets_per_project = max(1, len(all_bullets) // len(PROJECTS))

    MAX_POINTS_PER_PROJECT = 5

    for i, project in enumerate(PROJECTS, start=1):
        start_idx = (i - 1) * bullets_per_project
        end_idx = i * bullets_per_project if i < len(PROJECTS) else len(all_bullets)
        project_bullets = all_bullets[start_idx:end_idx][:MAX_POINTS_PER_PROJECT]  # 🚨 Add this slice
        updated_roles[project] = {
            f"point{j+1}": bullet for j, bullet in enumerate(project_bullets)
        }
        updated_roles[f"[DYNAMIC TECHNOLOGIES LIST {i}]"] = ", ".join(unique_subsets)

    # Get summary section
    try:
        existing_summary = extract_professional_summary(docx_path)
    except Exception as e:
        print(str(e))
        existing_summary = ""
        
    # TODO: currently we see this static line in final summary return by cohere in case this static line not present in final summary then append this static line to final summary
    # static line: Senior Software Engineer with 10 years of experience, proficient in Python, AWS, and SQL
    final_summary = merge_summary_with_job(existing_summary, description)
    final_summary = re.sub(r"\*\*|__", "", final_summary).replace("\n", " ").strip()
    updated_roles["Summary"] = final_summary

    output_path = Path(__file__).resolve().parent.parent / "output" / "generated_roles.py"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        f.write("updated_roles = {\n")
        for key, val in updated_roles.items():
            if isinstance(val, dict):
                f.write(f'    "{key}": {{\n')
                for k, v in val.items():
                    safe_v = v.replace('"', '\\"')
                    f.write(f'        "{k}": "{safe_v}",\n')
                f.write("    },\n")
            else:
                safe_val = val.replace('"', '\\"')
                f.write(f'    "{key}": "{safe_val}",\n')
        f.write("}\n")

    print(f"Generated roles saved to: {output_path}")
    return "✅ Success: Roles and summary saved."


# ---------- USAGE ---------- #
if __name__ == "__main__":
    
    docx_path = "noukri_dot_com_job_bot/input/Md_Irsad_ind.docx"
    
    jd = "About the job\nAbout the Role\nOverview:\nNewton School of Technology is on a mission to transform technology education and bridge the employability gap. As India’s first impact university, we are committed to revolutionizing learning, empowering students, and shaping the future of the tech industry. Backed by renowned professionals and industry leaders, we aim to solve the employability challenge and create a lasting impact on society.\nWe are currently looking for a\nData Engineer + Instructor– Data Mining\nto join our Computer Science Department. This is a full-time academic role focused on data mining, analytics, and teaching/mentoring students in core data science and engineering topics.\nKey Responsibilities:\n● Develop and deliver comprehensive and engaging lectures for the undergraduate \"Data Mining\", “BigData” and “Data Analytics” courses, covering the full syllabus from foundational concepts to advanced techniques.\n● Instruct students on the complete data lifecycle, including data preprocessing, cleaning, transformation, and feature engineering.\n● Teach the theory, implementation, and evaluation of a wide range of algorithms for Classification, Association rules mining, Clustering, and Anomaly detection.\n● Design and facilitate practical lab sessions and assignments that provide students with hands-on experience using modern data tools and software.\n● Develop and grade assessments, including assignments, projects, and examinations, that effectively measure the Course Learning Objectives (CLOs).\n● Mentor and guide students on projects, encouraging them to work with real-world or benchmark datasets (e.g., from Kaggle).\n● Stay current with the latest advancements, research, and industry trends in data engineering and machine learning to ensure the curriculum remains relevant and cutting-edge.\n● Contribute to the academic and research environment of the department and the university.\nRequired Qualifications:\n● A Ph.D. (or a Master's degree with significant, relevant industry experience) in Computer Science, Data Science, Artificial Intelligence, or a closely related field.\n● Demonstrable expertise in the core concepts of data engineering and machine learning as outlined in the syllabus.\n● Strong practical proficiency in Python and its data science ecosystem, specifically Scikit-learn, Pandas, NumPy, and visualization libraries (e.g., Matplotlib, Seaborn).\n● Proven experience in teaching, preferably at the undergraduate level, with an ability to make complex topics accessible and engaging.\n● Excellent communication and interpersonal skills.\nPreferred Qualifications:\n● A strong record of academic publications in reputable data mining, machine learning, or AI conferences/journals.\n● Prior industry experience as a Data Scientist, Big Data Engineer, Machine Learning Engineer, or in a similar role.\n● Experience with big data technologies (e.g., Spark, Hadoop) and/or deep learning frameworks (e.g., TensorFlow, PyTorch).\n● Experience in mentoring student teams for data science competitions or hackathons.\nPerks & Benefits:\n● Competitive salary packages aligned with industry standards.\n● Access to state-of-the-art labs and classroom facilities."
    
    generate_cv_roles(jd, docx_path)