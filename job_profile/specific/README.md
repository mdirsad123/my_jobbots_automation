# CV Automation Pipeline & Duplicate Tracker

A comprehensive CV generation system with 30-day duplicate detection for job applications.

## Overview

This system provides:
- **Master Prompt Template** for AI-driven CV tailoring
- **Duplicate Detection** using SHA-256 hashing to prevent accidental reapplications
- **Automatic Cleanup** of history older than 30 days
- **PDF & DOCX Generation** with strict 2-page formatting
- **Email Reply Generation** for professional job responses

## System Components

### 1. Master Prompt (`master_prompt.txt`)
AI instructions for:
- ATS keyword matching
- CV tailoring for specific job descriptions
- Dynamic file naming based on job slug and date
- Email reply generation
- 2-page layout enforcement

### 2. Duplicate Tracker (`jd_tracker.py`)
Python utility that:
- Calculates SHA-256 hash of JD content
- Maintains history in `jd_history.json`
- Detects duplicates within 30 days
- Auto-purges entries older than 30 days

### 3. Conversion Scripts
- `cv_to_pdf.py` - Generates PDF using ReportLab (9pt font)
- `cv_to_docx.py` - Generates DOCX using python-docx (matching PDF format)

Both scripts include integrated duplicate detection.

---

## File Naming Convention

### Input Files
```
<job_slug>_jd_<date>.txt
Example: idc_aba_jd_26_jul_2026.txt
```

### Output Files
```
md_irshad_cv_2page_<job_slug>_<date>.md      # Tailored CV (Markdown)
md_irshad_cv_2page_<job_slug>_<date>.pdf     # PDF version
md_irshad_cv_2page_<job_slug>_<date>.docx    # Word version
<job_slug>_jd_email_reply_<date>.txt         # Email draft

Example outputs for idc_aba_jd_26_jul_2026.txt:
- md_irshad_cv_2page_idc_aba_26_jul_2026.md
- md_irshad_cv_2page_idc_aba_26_jul_2026.pdf
- md_irshad_cv_2page_idc_aba_26_jul_2026.docx
- idc_aba_jd_email_reply_26_jul_2026.txt
```

---

## Quick Start Guide

### Step 1: Prepare Job Description
Save the JD as: `<job_slug>_jd_<date>.txt`
```bash
# Example
idc_aba_jd_26_jul_2026.txt
```

### Step 2: Tailor CV Using AI
Use `master_prompt.txt` with your AI assistant:
1. Paste JD into the prompt
2. AI will analyze and tailor the CV
3. AI will generate email reply
4. Outputs saved with dynamic naming

Example usage:
I have attached `master_prompt.txt` and JD into `idc_aba_jd_26_jul_2026.txt`
1. Analyze and tailor the CV
2. Generate email reply
3. Save Outputs (.md, .pdf, .docx)

Example usage in chatgpt:
i have attached specific(3).zip please follow specific\master_prompt.txt and JD into specific\company\idc_aba\idc_aba_jd_28_jul_2026.txt 
1. please generate downloadable link of email reply, .md file, .pdf, .docx, Interview preparation FAQs PDF file

link of irshadalamtech@gmail.com:
https://chatgpt.com/g/g-p-6a6071f3727c81918bcac8a6cf922752-knowledge-base-jobbot/c/6a65f565-8954-83ec-9914-5db2d2165b07

Example usage in gemini:
link of er.irshad26@gmail.com:
https://gemini.google.com/app/b8e3b14a960ce3b9?utm_source=app_launcher&utm_medium=owned&utm_campaign=base_all

### Step 3: Generate PDF & DOCX

#### Basic Usage (No Tracking)
```bash
cd job_profile/specific

# Generate PDF
python cv_to_pdf.py

# Generate DOCX
python cv_to_docx.py
```

#### With Duplicate Detection (Recommended)
```bash
cd job_profile/specific

# Generate PDF with tracking
python cv_to_pdf.py --input md_irshad_cv_2page_idc_aba_26_jul_2026.md --jd idc_aba_jd_26_jul_2026.txt

# Generate DOCX with tracking
python cv_to_docx.py --input md_irshad_cv_2page_idc_aba_26_jul_2026.md --jd idc_aba_jd_26_jul_2026.txt
```

#### Force Generation (Override Duplicate Warning)
```bash
python cv_to_pdf.py --input md_irshad_cv_2page_idc_aba_26_jul_2026.md --jd idc_aba_jd_26_jul_2026.txt --force

python cv_to_docx.py --input md_irshad_cv_2page_idc_aba_26_jul_2026.md --jd idc_aba_jd_26_jul_2026.txt --force
```

---

## Command Line Options

### `cv_to_pdf.py` / `cv_to_docx.py`

| Option | Short | Description | Required |
|--------|-------|-------------|----------|
| `--input` | `-i` | Input Markdown CV file | No (default: `md_irshad_cv_2page_company_x.md`) |
| `--jd` | | Job Description file for tracking | No (enables duplicate detection) |
| `--force` | `-f` | Force generation even if duplicate detected | No |

### Examples

```bash
# Basic PDF generation
python cv_to_pdf.py

# PDF with custom input
python cv_to_pdf.py --input my_cv.md

# PDF with duplicate tracking
python cv_to_pdf.py --input md_irshad_cv_2page_acme_15_jul_2026.md --jd acme_jd_15_jul_2026.txt

# Force generation (ignore duplicate warning)
python cv_to_pdf.py -i md_irshad_cv_2page_acme_15_jul_2026.md --jd acme_jd_15_jul_2026.txt -f
```

---

## Duplicate Detection System

### How It Works

1. **Hash Calculation**: SHA-256 hash of normalized JD content
2. **History Check**: Searches `jd_history.json` for matching hash within 30 days
3. **Warning Display**: If duplicate found, shows when it was previously processed
4. **Auto-Cleanup**: Removes entries older than 30 days on every run

### History File Format (`jd_history.json`)

```json
{
  "history": [
    {
      "jd_hash": "4323e22658d3bd5a7f8c9e1b2d4a5c6e...",
      "job_slug": "idc_aba",
      "timestamp": "2026-07-26T12:00:00",
      "generated_files": [
        "md_irshad_cv_2page_idc_aba_26_jul_2026.pdf",
        "md_irshad_cv_2page_idc_aba_26_jul_2026.docx"
      ]
    }
  ]
}
```

### Standalone Duplicate Check

Check if a JD was previously processed:
```bash
python jd_tracker.py idc_aba_jd_26_jul_2026.txt
```

Output:
```
[OK] No duplicate found (Hash: 4323e22658d3bd5a...)
```

Or if duplicate:
```
[X] DUPLICATE FOUND
  Previously processed: idc_aba
  Date: 2026-07-20T14:30:00
```

---

## Typical Workflow

### Complete Application Process

```bash
# 1. Save JD file
# File: idc_aba_jd_26_jul_2026.txt

# 2. Check for duplicates (optional)
python jd_tracker.py idc_aba_jd_26_jul_2026.txt

# 3. Use AI to tailor CV
# - Open master_prompt.txt in AI assistant
# - Paste JD content
# - AI generates tailored MD file and email reply

# 4. Generate PDF with tracking
python cv_to_pdf.py --input md_irshad_cv_2page_idc_aba_26_jul_2026.md --jd idc_aba_jd_26_jul_2026.txt

# 5. Generate DOCX with tracking
python cv_to_docx.py --input md_irshad_cv_2page_idc_aba_26_jul_2026.md --jd idc_aba_jd_26_jul_2026.txt

# 6. Review email reply
# File: idc_aba_jd_email_reply_26_jul_2026.txt

# 7. Send application with attachments:
# - md_irshad_cv_2page_idc_aba_26_jul_2026.pdf
# - md_irshad_cv_2page_idc_aba_26_jul_2026.docx
```

---

## Technical Details

### Dependencies

Install via shared Poetry environment:
```bash
cd C:\Users\erirs\projects\common_venv_py312
poetry add reportlab python-docx
poetry install
```

### Python Version
- Python 3.12+
- Uses shared venv: `C:\Users\erirs\projects\common_venv_py312\.venv`

### 2-Page Layout Constraints
- Font: Arial / Helvetica 9.0pt
- Margins: Top/Bottom 0.35", Left/Right 0.4"
- Max bullets per major role: 4
- Max bullets per mid role: 3
- Single-line bullets: 65-85 characters

### Hash Normalization
JD content is normalized before hashing:
- Strips leading/trailing whitespace
- Collapses multiple spaces
- Ensures consistent hash generation

---

## Troubleshooting

### Issue: "Input file not found"
**Solution**: Check file path and ensure you're in the correct directory
```bash
cd c:\Users\erirs\projects\ird-projects\knowledge-base-jobbot\job_profile\specific
```

### Issue: Duplicate warning when reapplying
**Solution 1**: Review if this is intentional (e.g., following up)
**Solution 2**: Use `--force` flag to override
```bash
python cv_to_pdf.py --input <file>.md --jd <jd>.txt --force
```

### Issue: History file corruption
**Solution**: Delete `jd_history.json` to reset tracking
```bash
del jd_history.json  # Windows
rm jd_history.json   # Linux/Mac
```

### Issue: PDF/DOCX exceeds 2 pages
**Solution**: Reduce bullet points in the Markdown CV:
- Keep 3-4 bullets per major role
- Keep 2-3 bullets per other roles
- Shorten bullet text to 65-85 characters

---

## File Structure

```
job_profile/specific/
├── master_prompt.txt                    # AI instructions
├── jd_tracker.py                        # Duplicate detection utility
├── cv_to_pdf.py                         # PDF generator
├── cv_to_docx.py                        # DOCX generator
├── md_irshad_cv_2page_company_x.md      # Base CV template
├── jd_history.json                      # Tracking history (auto-generated)
├── README.md                            # This file
│
└── company/                             # Company-specific folders
    ├── <company_slug>/                  # One folder per company/job
    │   ├── <job_slug>_jd_<date>.txt             # Job description
    │   ├── md_irshad_cv_2page_<slug>_<date>.md  # Tailored CV (Markdown)
    │   ├── md_irshad_cv_2page_<slug>_<date>.pdf # PDF output
    │   ├── md_irshad_cv_2page_<slug>_<date>.docx# DOCX output
    │   └── <job_slug>_jd_email_reply_<date>.txt # Email draft
    │
    └── idc_aba/                         # Example company folder
        ├── idc_aba_jd_26_jul_2026.txt
        ├── md_irshad_cv_2page_idc_aba_26_jul_2026.md
        ├── md_irshad_cv_2page_idc_aba_26_jul_2026.pdf
        ├── md_irshad_cv_2page_idc_aba_26_jul_2026.docx
        └── idc_aba_jd_email_reply_26_jul_2026.txt
```

**Note:** Company-specific files are organized in subdirectories under `company/` for better organization and easier file management.

---

## Best Practices

1. **Always use tracking** when generating CVs for job applications
2. **Review duplicate warnings** - they prevent accidental reapplications
3. **Keep JD files** for at least 30 days for tracking accuracy
4. **Maintain naming convention** for automatic slug/date extraction
5. **Backup `jd_history.json`** periodically for audit trail
6. **Test 2-page fit** before sending applications
7. **Customize email reply** before sending (it's a template)

---

## License & Support

This is an internal tool for CV automation and job application tracking.

For issues or enhancements:
1. Check this README first
2. Review `master_prompt.txt` for AI capabilities
3. Test with `--help` flag for command options

---

## Changelog

### v1.0 (2026-07-26)
- Initial implementation
- SHA-256 duplicate detection
- 30-day auto-cleanup
- Integrated tracking in PDF/DOCX generators
- Master prompt updates for email generation
- Dynamic file naming support

5️⃣ Recommended daily workflow (very important)
🔁 Switching between Cline and Codex safely
Before starting work (Codex)
Use this starter prompt (copy-paste):
Read ALL Memory Bank files first.
Summarize current project state and active goals.
Propose a short plan before coding.
This aligns Codex with how Cline already works.
Before starting work (Cline)
follow your custom instructions the write task/prompt to ask cline 
initialize memory bank - Use when starting a new project
After a milestone
If using Cline:
update memory bank
If using Codex:
👉 This keeps memory consistent across tools
Update memory bank.
Review all files.
Append updates to activeContext.md and progress.md.