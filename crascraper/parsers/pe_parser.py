"""
Parse CRA Performance Evaluation PDFs into structured data.
"""
import re
from typing import Optional
from crascraper.data.schema import PerformanceEvaluation, CRA_RATINGS


def parse_pe_pdf(pdf_path: str) -> Optional[PerformanceEvaluation]:
    """
    Parse a CRA Performance Evaluation PDF into structured data.

    Requires pdfplumber: pip install pdfplumber

    Args:
        pdf_path: Path to the PE PDF file

    Returns:
        PerformanceEvaluation with extracted fields, or None if parse fails
    """
    try:
        import pdfplumber
    except ImportError:
        raise ImportError(
            "pdfplumber is required to parse PE PDFs. "
            "Install with: pip install pdfplumber"
        )

    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"
    except Exception as e:
        print(f"PDF parse error: {e}")
        return None

    return parse_pe_text(text)


def parse_pe_text(text: str) -> Optional[PerformanceEvaluation]:
    """
    Parse Performance Evaluation text into structured data.
    Used when PDF text has already been extracted.
    """
    if not text or len(text) < 100:
        return None

    bank_name = _extract_bank_name(text)
    bank_id = _extract_bank_id(text)
    exam_date = _extract_exam_date(text)
    overall_rating = _extract_overall_rating(text)
    regulator = _extract_regulator(text)
    test_ratings = _extract_test_ratings(text)
    assessment_areas = _extract_assessment_areas(text)

    return PerformanceEvaluation(
        bank_id=bank_id or "",
        bank_name=bank_name or "Unknown",
        exam_date=exam_date or "",
        overall_rating=overall_rating or "Unknown",
        regulator=regulator or "Unknown",
        assessment_areas=assessment_areas,
        lending_test_rating=test_ratings.get("lending"),
        investment_test_rating=test_ratings.get("investment"),
        service_test_rating=test_ratings.get("service"),
        community_development_rating=test_ratings.get("community_development"),
        raw_text=text[:5000],  # store first 5000 chars for reference
    )


def _extract_bank_name(text: str) -> Optional[str]:
    patterns = [
        r"PUBLIC DISCLOSURE\s+(?:[A-Z]+\s+\d+,\s+\d{4}\s+)?([A-Z][A-Za-z &,\.\-]+(?:Bank|N\.A\.|Trust|Federal|Savings)[A-Za-z &,\.\-]*)",
        r"Institution:\s+([A-Z][A-Za-z &,\.\-]+)",
        r"BANK NAME:\s*([A-Za-z &,\.\-]+)",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1).strip()
    return None


def _extract_bank_id(text: str) -> Optional[str]:
    patterns = [
        r"Charter Number:\s*(\d+)",
        r"Certificate Number:\s*(\d+)",
        r"FDIC Certificate.*?(\d{4,6})",
        r"RSSD ID:\s*(\d+)",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1)
    return None


def _extract_exam_date(text: str) -> Optional[str]:
    m = re.search(
        r"(?:Date of Evaluation|Examination Date|Date of Exam):\s*"
        r"(\w+\s+\d+,\s+\d{4}|\d{1,2}/\d{1,2}/\d{4})",
        text
    )
    if m:
        return m.group(1).strip()

    m = re.search(r"PUBLIC DISCLOSURE\s+(\w+\s+\d+,\s+\d{4})", text)
    if m:
        return m.group(1).strip()

    return None


def _extract_overall_rating(text: str) -> Optional[str]:
    patterns = [
        r"INSTITUTION'?S?\s+CRA RATING:\s*\"?([A-Z][A-Za-z\s]+?)\"?[\.\n]",
        r"Overall Rating:\s*([A-Z][A-Za-z\s]+?)[\.\n]",
        r"Overall CRA rating:\s*([A-Z][A-Za-z\s]+?)[\.\n]",
        r'rating of\s*"?([A-Z][a-z][A-Za-z\s]+?)"?[\.\n]',
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            rating = m.group(1).strip()
            for canonical in CRA_RATINGS:
                if canonical.lower() in rating.lower():
                    return canonical
    return None


def _extract_regulator(text: str) -> Optional[str]:
    if re.search(r"Office of the Comptroller of the Currency|OCC", text):
        return "OCC"
    if re.search(r"Federal Reserve|Reserve Bank", text):
        return "FRS"
    if re.search(r"Federal Deposit Insurance Corporation|FDIC", text):
        return "FDIC"
    return None


def _extract_test_ratings(text: str) -> dict:
    """Extract individual test ratings (lending, investment, service)."""
    ratings = {}
    patterns = {
        "lending":              r"Lending Test:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        "investment":           r"Investment Test:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        "service":              r"Service Test:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        "community_development": r"Community Development Test:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
    }
    for key, pat in patterns.items():
        m = re.search(pat, text)
        if m:
            value = m.group(1).strip()
            for canonical in CRA_RATINGS:
                if canonical.lower().split()[0] in value.lower():
                    ratings[key] = canonical
                    break
    return ratings


def _extract_assessment_areas(text: str) -> list:
    """Extract assessment area names from PE text."""
    areas = []
    section = re.search(
        r"(?:ASSESSMENT AREAS?|Assessment Areas?):?\s*\n(.*?)"
        r"(?:CONCLUSIONS|RATINGS|SCOPE|Lending Test)",
        text, re.DOTALL | re.IGNORECASE
    )
    if section:
        section_text = section.group(1)
        msa_pattern = r"([A-Z][A-Za-z\s\-,]+(?:MSA|MD|Metropolitan|MD)\s*(?:#?\d+)?)"
        for match in re.finditer(msa_pattern, section_text):
            area = match.group(1).strip()
            if area not in areas and len(area) < 100:
                areas.append(area)
    return areas[:20]
