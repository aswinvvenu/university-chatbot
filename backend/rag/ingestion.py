"""
Document Ingestion Pipeline
Handles PDF, CSV/Excel, and plain text ingestion for RAG.
"""
import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any

import pdfplumber
import pandas as pd


DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "docs")


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text content from a PDF file."""
    text_parts = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    text_parts.append(f"[Page {page_num}]\n{text}")
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
    return "\n\n".join(text_parts)


def extract_text_from_csv_excel(file_path: str) -> str:
    """Extract and format data from CSV or Excel files."""
    try:
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        # Convert dataframe to readable text
        text_parts = []
        filename = Path(file_path).stem.replace("_", " ").title()
        text_parts.append(f"Data from {filename}:\n")

        # Add column descriptions
        text_parts.append(f"Columns: {', '.join(df.columns.tolist())}\n")

        # Convert each row to readable format
        for _, row in df.iterrows():
            row_text = " | ".join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
            text_parts.append(row_text)

        return "\n".join(text_parts)
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ""


def load_all_documents() -> List[Dict[str, Any]]:
    """Load all documents from the docs directory."""
    documents = []

    if not os.path.exists(DOCS_DIR):
        os.makedirs(DOCS_DIR)
        print(f"Created docs directory at {DOCS_DIR}")
        return documents

    for filename in os.listdir(DOCS_DIR):
        file_path = os.path.join(DOCS_DIR, filename)
        source = filename
        content = ""

        if filename.endswith(".pdf"):
            print(f"  Ingesting PDF: {filename}")
            content = extract_text_from_pdf(file_path)
        elif filename.endswith((".csv", ".xlsx", ".xls")):
            print(f"  Ingesting spreadsheet: {filename}")
            content = extract_text_from_csv_excel(file_path)
        elif filename.endswith(".txt"):
            print(f"  Ingesting text: {filename}")
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            continue

        if content.strip():
            documents.append({
                "source": source,
                "content": content,
                "file_path": file_path
            })

    return documents
