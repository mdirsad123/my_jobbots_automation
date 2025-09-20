import re
import os
import sys

# Add the project root to import local modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from utils.technology_resole_resp import tech_roles_responsibilities

def extract_key_skills(description: str) -> list[str]:
    words = description.split()
    lowercase_words = [word.lower() for word in words]
    lowercase_description = ' '.join(lowercase_words)

    tech_roles = {
        key.lower(): value for key, value in tech_roles_responsibilities.items()
    }

    matched_techs = []
    for tech_key in tech_roles:
        if tech_key in lowercase_description:
            matched_techs.append(tech_key)

    return matched_techs


# ---------- USAGE ---------- #
if __name__ == "__main__":
    jd = """About the job
    Overview: Newton School of Technology ... 
    Required Qualifications:
    ● Strong practical proficiency in Python and its data science ecosystem,
    specifically Scikit-learn, Pandas, NumPy, and visualization libraries (e.g., Matplotlib, Seaborn).
    ● Experience with big data technologies (e.g., Spark, Hadoop) and/or deep learning frameworks (e.g., TensorFlow, PyTorch).
    ● Prior industry experience as a Data Scientist, Big Data Engineer, Machine Learning Engineer, or in a similar role."""

    key_skills = extract_key_skills(jd)
    print("Extracted Key Skills:")
    for skill in key_skills:
        print(f"- {skill}")
