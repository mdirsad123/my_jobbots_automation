"""
cd job_profile/specific
# Replace <company_slug> and <date> with actual values
python cv_to_pdf.py --input company/<company_slug>/md_irshad_cv_2page_<company_slug>_<date>.md --jd company/<company_slug>/<company_slug>_jd_<date>.txt

Convert Markdown CV to PDF using ReportLab - Strict 2-Page Layout
Fixed parser with XML character escaping and HTML comment filtering.
Now includes 30-day duplicate detection via JD hash tracking.
"""
import os
import re
import argparse
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.colors import HexColor, white

# Import duplicate tracking utility
from jd_tracker import JDTracker, extract_job_slug_from_filename, extract_date_from_filename

def clean_markdown_for_reportlab(text):
    """
    Safely converts Markdown syntax to ReportLab XML-compatible markup.
    Escapes XML entities (&, <, >) and converts bold/italic/link formatting.
    """
    # 1. Escape ampersands that aren't already valid XML entities
    text = re.sub(r'&(?![a-zA-Z0-9#]+;)', '&amp;', text)
    
    # 2. Convert Markdown links [Text](URL) to ReportLab link tags
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" color="#2c5aa0"><u>\1</u></a>', text)
    
    # 3. Convert **bold** to <b>bold</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    
    # 4. Convert *italic* to <i>italic</i>
    text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<i>\1</i>', text)
    
    return text

def parse_markdown_to_pdf(md_file, pdf_file):
    """Convert markdown CV to PDF with strict 2-page layout"""
    
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Strip out HTML comment blocks (e.g. <!-- ... -->) so ReportLab ignores metadata
    content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
    
    # Create PDF document with tight margins for 2-page fit
    doc = SimpleDocTemplate(
        pdf_file,
        pagesize=letter,
        topMargin=0.30 * inch,
        bottomMargin=0.30 * inch,
        leftMargin=0.40 * inch,
        rightMargin=0.40 * inch
    )
    
    styles = getSampleStyleSheet()
    
    # Typography Styles (Font size 9.0pt, strict 2 pages)
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=15,
        textColor=HexColor('#1a1a1a'),
        spaceAfter=2,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=HexColor('#2c5aa0'),
        spaceAfter=3,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    contact_style = ParagraphStyle(
        'ContactStyle',
        parent=styles['Normal'],
        fontSize=8.5,
        textColor=HexColor('#333333'),
        spaceAfter=3,
        alignment=TA_CENTER
    )
    
    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=10.5,
        textColor=HexColor('#1a1a1a'),
        spaceAfter=2,
        spaceBefore=3,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT
    )
    
    heading3_style = ParagraphStyle(
        'CustomHeading3',
        parent=styles['Heading3'],
        fontSize=9.5,
        textColor=HexColor('#1a1a1a'),
        spaceAfter=1,
        spaceBefore=2,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT
    )
    
    # White text on dark blue banner for projects
    project_name_style = ParagraphStyle(
        'ProjectNameStyle',
        parent=styles['Normal'],
        fontSize=9.5,
        textColor=white,
        spaceAfter=0,
        spaceBefore=0,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT,
        backColor=HexColor('#1A365D'),
        leftIndent=4,
        rightIndent=4
    )
    
    key_contributions_style = ParagraphStyle(
        'KeyContributionsStyle',
        parent=styles['Normal'],
        fontSize=9.0,
        textColor=white,
        spaceAfter=0,
        spaceBefore=0,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT,
        backColor=HexColor('#2C5AA0'),
        leftIndent=4,
        rightIndent=4
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=9.0,
        textColor=HexColor('#333333'),
        spaceAfter=1.5,
        leading=11.0,
        alignment=TA_LEFT
    )
    
    bullet_style = ParagraphStyle(
        'CustomBullet',
        parent=styles['Normal'],
        fontSize=9.0,
        textColor=HexColor('#333333'),
        leftIndent=12,
        spaceAfter=1.0,
        leading=11.0
    )
    
    date_style = ParagraphStyle(
        'DateStyle',
        parent=styles['Normal'],
        fontSize=8.5,
        textColor=HexColor('#555555'),
        spaceAfter=1.5,
        alignment=TA_LEFT
    )
    
    story = []
    lines = content.split('\n')
    i = 0
    
    # Generic regex pattern matching project header lines like "**PROJECT_NAME – Description**"
    PROJECT_PATTERN_REGEX = re.compile(r'^\*\*([A-Z0-9_\s\/]+)\s*[–\-]\s*(.*)\*\*$', re.IGNORECASE)
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue

        # Candidate Name (# **NAME**)
        if line.startswith('# **') and line.endswith('**'):
            text = clean_markdown_for_reportlab(line[4:-2])
            story.append(Paragraph(text, title_style))
        
        # Subtitle (Job Title)
        elif line.startswith('**') and line.endswith('**') and '|' in line and not line.startswith('### **'):
            text = clean_markdown_for_reportlab(line[2:-2])
            story.append(Paragraph(text, subtitle_style))
            
        # Contact Information
        elif '📞' in line or '✉️' in line or '🔗' in line or '💻' in line:
            text = line.replace('📞', '').replace('✉️', '').replace('🔗', '').replace('💻', '')
            text = clean_markdown_for_reportlab(text)
            story.append(Paragraph(text, contact_style))
        
        # Horizontal Rule
        elif line.startswith('---'):
            story.append(Spacer(1, 0.01 * inch))
        
        # Section Heading (## **TEXT**)
        elif line.startswith('## **') and line.endswith('**'):
            text = clean_markdown_for_reportlab(line[5:-2])
            story.append(Spacer(1, 0.01 * inch))
            story.append(Paragraph(f'<b>{text}</b>', heading2_style))
        
        # Company / Role Heading (### **TEXT**)
        elif line.startswith('### **') and line.endswith('**'):
            text = clean_markdown_for_reportlab(line[6:-2])
            story.append(Paragraph(f'<b>{text}</b>', heading3_style))
        
        # Employment Dates (*Date Range*)
        elif line.startswith('*') and line.endswith('*') and ('–' in line or '-' in line):
            text = clean_markdown_for_reportlab(line[1:-1])
            story.append(Paragraph(f'<i>{text}</i>', date_style))
        
        # GENERIC PROJECT BANNERS: Matches any "**PROJECT NAME - Description**" format
        elif PROJECT_PATTERN_REGEX.match(line):
            text = clean_markdown_for_reportlab(line[2:-2])
            story.append(Spacer(1, 0.01 * inch))
            story.append(Paragraph(text, project_name_style))
            story.append(Spacer(1, 0.01 * inch))
        
        # Key Contributions Header
        elif line == '**Key Contributions:**':
            story.append(Spacer(1, 0.01 * inch))
            story.append(Paragraph('Key Contributions:', key_contributions_style))
            story.append(Spacer(1, 0.01 * inch))
        
        # Bullet points (- or ✓)
        elif line.startswith('- ') or line.startswith('✓ '):
            text = clean_markdown_for_reportlab(line[2:].strip())
            story.append(Paragraph(f'• {text}', bullet_style))
        
        # Regular Body Text & Skills Lines
        else:
            text = clean_markdown_for_reportlab(line)
            story.append(Paragraph(text, body_style))
        
        i += 1
    
    doc.build(story)
    print(f"[SUCCESS] Generated 2-Page PDF with 9.0pt Font: {pdf_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Convert Markdown CV to PDF with duplicate JD tracking',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage (no tracking):
  python cv_to_pdf.py
  
  # With JD tracking:
  python cv_to_pdf.py --input md_irshad_cv_2page_idc_aba_26_jul_2026.md --jd idc_aba_jd_26_jul_2026.txt
  
  # Force generation even if duplicate detected:
  python cv_to_pdf.py --input md_irshad_cv_2page_idc_aba_26_jul_2026.md --jd idc_aba_jd_26_jul_2026.txt --force
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        type=str,
        help='Input Markdown CV file (default: md_irshad_cv_2page_company_x.md)'
    )
    
    parser.add_argument(
        '--jd',
        type=str,
        help='Job Description file for duplicate tracking (optional)'
    )
    
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Force generation even if duplicate JD detected'
    )
    
    args = parser.parse_args()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Determine input file
    if args.input:
        input_md = args.input if os.path.isabs(args.input) else os.path.join(script_dir, args.input)
    else:
        input_md = os.path.join(script_dir, "md_irshad_cv_2page_company_x.md")
    
    # Check if input file exists
    if not os.path.exists(input_md):
        print(f"[ERROR] Input file not found: {input_md}")
        exit(1)
    
    # Determine output filename (save in same directory as input file)
    input_basename = os.path.splitext(os.path.basename(input_md))[0]
    input_dir = os.path.dirname(input_md)
    output_pdf = os.path.join(input_dir, f"{input_basename}.pdf")
    
    print("\n" + "="*70)
    print("  CV to PDF Converter with Duplicate JD Tracking")
    print("="*70)
    
    # JD Tracking Logic
    if args.jd:
        jd_file = args.jd if os.path.isabs(args.jd) else os.path.join(script_dir, args.jd)
        
        if not os.path.exists(jd_file):
            print(f"[WARNING] JD file not found: {jd_file}")
            print("[INFO] Proceeding without duplicate tracking")
        else:
            # Initialize tracker
            tracker = JDTracker(history_file=os.path.join(script_dir, "jd_history.json"))
            
            # Extract job slug for tracking
            job_slug = extract_job_slug_from_filename(jd_file)
            
            # Expected output files (in same directory as input)
            output_docx = os.path.join(input_dir, f"{input_basename}.docx")
            generated_files = [
                os.path.basename(output_pdf),
                os.path.basename(output_docx)
            ]
            
            # Check for duplicates
            should_proceed, warning = tracker.process_jd(
                jd_file_path=jd_file,
                job_slug=job_slug,
                generated_files=generated_files,
                force=args.force
            )
            
            if not should_proceed:
                # Safe console output for Windows (handles Unicode characters)
                safe_warning = warning.encode('ascii', 'replace').decode('ascii')
                print(safe_warning)
                print("\n[ABORTED] PDF generation cancelled due to duplicate JD.")
                print("Use --force flag to override this check.")
                exit(0)
    
    # Generate PDF
    print(f"\n[INPUT]  Markdown: {os.path.basename(input_md)}")
    print(f"[OUTPUT] PDF: {os.path.basename(output_pdf)}")
    print("\n" + "-"*70)
    
    parse_markdown_to_pdf(input_md, output_pdf)
    
    print("-"*70)
    print(f"\n[OK] PDF generation complete!")
    print(f"  Location: {output_pdf}")
    print("\n" + "="*70 + "\n")
