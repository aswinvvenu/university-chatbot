#!/usr/bin/env python3
"""Convert text documents to PDF for use as RAG knowledge sources."""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.colors import HexColor
import os

DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "docs")


def text_to_pdf(input_txt: str, output_pdf: str):
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=letter,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=inch
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=HexColor("#1a3c5e"),
        spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=HexColor("#2d6a9f"),
        spaceAfter=8,
        spaceBefore=12,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        spaceAfter=6,
    )

    story = []

    with open(input_txt, "r") as f:
        lines = f.readlines()

    for line in lines:
        line = line.rstrip()
        if not line:
            story.append(Spacer(1, 6))
            continue

        # Detect heading levels
        if line.isupper() and len(line) > 3:
            if len(line) > 40:
                story.append(Paragraph(line.replace("&", "&amp;"), title_style))
            else:
                story.append(Paragraph(line.replace("&", "&amp;"), heading_style))
        elif line.startswith("Q:") or line.startswith("A:"):
            bold_style = ParagraphStyle(
                "Bold",
                parent=body_style,
                fontName="Helvetica-Bold" if line.startswith("Q:") else "Helvetica",
            )
            story.append(Paragraph(line.replace("&", "&amp;").replace("<", "&lt;"), bold_style))
        else:
            story.append(Paragraph(
                line.replace("&", "&amp;").replace("<", "&lt;"),
                body_style
            ))

    doc.build(story)
    print(f"Created: {output_pdf}")


if __name__ == "__main__":
    # Convert admissions guide
    text_to_pdf(
        os.path.join(DOCS_DIR, "admissions_guide.txt"),
        os.path.join(DOCS_DIR, "admissions_guide.pdf")
    )
    # Convert academic programs
    text_to_pdf(
        os.path.join(DOCS_DIR, "academic_programs.txt"),
        os.path.join(DOCS_DIR, "academic_programs.pdf")
    )
    print("PDF generation complete!")
