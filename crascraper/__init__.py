from crascraper._version import __version__
from crascraper.data.schema import (
    CRARating, BankRatingHistory, PerformanceEvaluation,
    CRA_RATINGS, RATING_SCORES, REGULATORS, EXAM_METHODS,
)
from crascraper.exceptions import (
    CRAScraperError, FFIECAccessError, FFIECParseError,
)
from crascraper.scrapers.ffiec import search_ratings
from crascraper.parsers.pe_parser import parse_pe_pdf, parse_pe_text
from crascraper.analysis.insights import (
    to_dataframe, rating_distribution, rating_by_state, rating_by_regulator,
    find_partnership_opportunities, build_history, find_downgrades,
    summary_report,
)

__all__ = [
    "CRARating", "BankRatingHistory", "PerformanceEvaluation",
    "CRAScraperError", "FFIECAccessError", "FFIECParseError",
    "search_ratings",
    "parse_pe_pdf", "parse_pe_text",
    "to_dataframe", "rating_distribution",
    "rating_by_state", "rating_by_regulator",
    "find_partnership_opportunities",
    "build_history", "find_downgrades",
    "summary_report",
    "CRA_RATINGS", "RATING_SCORES", "REGULATORS", "EXAM_METHODS",
]
