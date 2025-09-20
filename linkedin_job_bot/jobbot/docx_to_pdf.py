"""
python linkedin_job_bot/jobbot/docx_to_pdf.py
"""

import os
import shutil
from pathlib import Path
import sys

# Step 1: Add MiKTeX bin directory
miktex_bin = r"C:\Program Files\MiKTeX\miktex\bin\x64"
if miktex_bin not in os.environ["PATH"]:
    os.environ["PATH"] += os.pathsep + miktex_bin
    print(f"Added to PATH: {miktex_bin}")

# Step 2: Set Proxy Authentication
# Replace with your actual proxy server and credentials
proxy_username = "your_username"
proxy_password = "your_password"
proxy_server = "proxy.yourcompany.com"
proxy_port = "8080"

proxy_auth = f"http://{proxy_username}:{proxy_password}@{proxy_server}:{proxy_port}"
os.environ["http_proxy"] = proxy_auth
os.environ["https_proxy"] = proxy_auth
print("✅ Proxy authentication configured.")

# Step 3: Set Pandoc executable via environment variable
pandoc_executable = r"C:\Users\erirs\AppData\Local\Pandoc\pandoc.exe"
if not Path(pandoc_executable).exists():
    print(f"❌ Error: Pandoc executable not found at {pandoc_executable}")
    sys.exit(1)
os.environ["PYPANDOC_PANDOC"] = pandoc_executable
print(f"✅ Pandoc path set explicitly to: {pandoc_executable}")

# Import pypandoc after setting proxy and pandoc path
import pypandoc

def verify_executable(executable_name):
    path = shutil.which(executable_name)
    print(f"{executable_name} found at: {path}")
    return path

def convert_docx_to_pdf(input_docx: str, output_pdf: str = None) -> str:
    input_path = Path(input_docx).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input DOCX file not found: {input_path}")

    if output_pdf is None:
        output_path = input_path.with_suffix('.pdf')
    else:
        output_path = Path(output_pdf).resolve()

    try:
        output = pypandoc.convert_file(
            source_file=str(input_path),
            to='pdf',
            outputfile=str(output_path),
            extra_args=['--pdf-engine=xelatex']
        )
        if not output_path.exists():
            raise RuntimeError(f"Conversion failed. PDF not created at: {output_path}")
        print(f"✅ PDF generated successfully: {output_path}")
        return str(output_path)
    except Exception as e:
        raise RuntimeError(f"❌ Conversion failed: {e}")

if __name__ == "__main__":
    if not verify_executable("xelatex"):
        print("❌ Error: xelatex not found in PATH.")
        sys.exit(1)

    input_docx = r"D:\ird-projects\my_pyautomation\ui\driver\chromedriver.exe"
    try:
        pdf_path = convert_docx_to_pdf(input_docx)
        print(f"📄 PDF saved at: {pdf_path}")
    except Exception as e:
        print(f"❌ Error during conversion: {e}")
