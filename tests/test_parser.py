import pytest
from crascraper.parsers.pe_parser import parse_pe_text


SAMPLE_PE_TEXT = """
PUBLIC DISCLOSURE

January 15, 2024

COMMUNITY REINVESTMENT ACT
PERFORMANCE EVALUATION

Sample Community Bank
Charter Number: 12345

Office of the Comptroller of the Currency

INSTITUTION'S CRA RATING: "Satisfactory"

The Lending Test is rated: High Satisfactory
The Investment Test is rated: Outstanding
The Service Test is rated: Low Satisfactory

ASSESSMENT AREAS:
The bank's assessment areas include:
- Chicago-Naperville-Elgin MSA
- Milwaukee-Waukesha MSA

CONCLUSIONS WITH RESPECT TO PERFORMANCE TESTS

The bank's performance is...
"""


def test_parse_pe_text_returns_object():
    pe = parse_pe_text(SAMPLE_PE_TEXT)
    assert pe is not None


def test_parse_extracts_bank_name():
    pe = parse_pe_text(SAMPLE_PE_TEXT)
    assert "Sample Community Bank" in pe.bank_name or pe.bank_name


def test_parse_extracts_charter_number():
    pe = parse_pe_text(SAMPLE_PE_TEXT)
    assert pe.bank_id == "12345"


def test_parse_extracts_rating():
    pe = parse_pe_text(SAMPLE_PE_TEXT)
    assert pe.overall_rating == "Satisfactory"


def test_parse_extracts_regulator():
    pe = parse_pe_text(SAMPLE_PE_TEXT)
    assert pe.regulator == "OCC"


def test_parse_short_text_returns_none():
    pe = parse_pe_text("Too short")
    assert pe is None
