# pdf_processor.py
import pdfplumber
import re
from typing import Dict, List

def extract_text_from_pdf(pdf_path: str) -> Dict:
    """Extract text from PDF with optimized cleaning"""
    
    text_by_page = {}
    full_text = ""

    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Process only first 50 pages for speed
            max_pages = min(len(pdf.pages), 50)
            
            for page_num in range(max_pages):
                page = pdf.pages[page_num]
                text = page.extract_text() or ""
                
                if isinstance(text, (bytes, bytearray)):
                    text = text.decode('utf-8', errors='ignore')
                
                if text.strip():
                    text_by_page[page_num + 1] = text
                    full_text += text + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return {
            "full_text": "",
            "pages": {},
            "sections": [],
            "word_count": 0
        }

    # Quick cleaning
    full_text = clean_text(full_text)
    
    # Quick section detection
    sections = detect_sections(full_text)

    return {
        "full_text": full_text,
        "pages": text_by_page,
        "sections": sections,
        "word_count": len(full_text.split())
    }


def clean_text(text: str) -> str:
    """Fast text cleaning"""
    if not text:
        return ""
    
    if isinstance(text, (bytes, bytearray)):
        text = text.decode('utf-8', errors='ignore')
    
    # Fast cleaning operations
    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'\S+@\S+', '', text)
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def detect_sections(text: str) -> List[str]:
    """Quick section detection"""
    section_keywords = {
        'abstract', 'introduction', 'methodology', 'methods', 
        'results', 'findings', 'discussion', 'conclusion'
    }
    
    detected = set()
    text_lower = text[:5000].lower()  # Check only first 5000 chars
    
    for keyword in section_keywords:
        if keyword in text_lower:
            detected.add(keyword)
    
    return list(detected)