"""
python -m noukrigulf_job_bot.jobbot.compress_pdf_file
"""

import fitz  # PyMuPDF
from PIL import Image
import io
import logging

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
    
import subprocess
import os

def compress_pdf_ghostscript(input_path, output_path, quality="screen"):
    """
    Compress PDF using Ghostscript.
    quality: 'screen' (smallest), 'ebook', 'printer', 'prepress'
    """
    try:
        gs_command = [
            "gswin64c",  # for Windows 64-bit. Use "gs" on Linux/Mac
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            f"-dPDFSETTINGS=/{quality}",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            f"-sOutputFile={output_path}",
            input_path,
        ]
        subprocess.run(gs_command, check=True)
        print(f"✅ Compressed PDF saved to: {output_path}")
        return output_path
    except Exception as e:
        print(f"❌ Ghostscript compression failed: {e}")
        return input_path

if __name__ == '__main__':
    input_pdf_path = r"D:\ird-projects\my_pyautomation\noukrigulf_job_bot\output\Md_Irsad_confidential_company.pdf"
    output_pdf_path = input_pdf_path.replace(".pdf", "_cv.pdf")
    quality="screen"
    result_path = compress_pdf_ghostscript(input_pdf_path, output_pdf_path, quality)
    print(f"Compressed PDF saved to: {result_path}")