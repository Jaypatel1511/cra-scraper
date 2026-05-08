"""
Core dataclasses and constants for CRA exam data.
Based on FFIEC CRA Ratings Database and OCC/FDIC/Federal Reserve PE reports.
"""
from dataclasses import dataclass, field
from typing import Optional


CRA_RATINGS = {
    "Outstanding":              "Strong CRA performance",
    "Satisfactory":             "Adequate CRA performance",
    "Needs to Improve":         "Weak CRA performance",
    "Substantial Noncompliance": "Inadequate CRA performance",
}

RATING_SCORES = {
    "Outstanding":              4,
    "Satisfactory":             3,
    "Needs to Improve":         2,
    "Substantial Noncompliance": 1,
}

REGULATORS = {
    "OCC":  "Office of the Comptroller of the Currency",
    "FRS":  "Federal Reserve System",
    "FDIC": "Federal Deposit Insurance Corporation",
    "OTS":  "Office of Thrift Supervision (defunct, pre-2011)",
}

EXAM_METHODS = {
    "Small Bank":               "Small institution exam method",
    "Intermediate Small Bank":  "Intermediate small institution method",
    "Large Bank":               "Large institution exam method",
    "Wholesale":                "Wholesale institution community development test",
    "Limited Purpose":          "Limited purpose institution community development test",
    "Strategic Plan":           "Strategic plan exam method",
}

ASSET_RANGES = {
    "small":              (0,             1_564_000_000),
    "intermediate_small": (391_000_000,   1_564_000_000),
    "large":              (1_564_000_000, float("inf")),
}

FFIEC_BASE = "https://www.ffiec.gov/craratings"
FFIEC_SEARCH_URL = f"{FFIEC_BASE}/InstitutionRatingSearch.aspx"
FFIEC_RESULTS_URL = f"{FFIEC_BASE}/InstitutionRatingsSearchResults.aspx"

OCC_BASE = "https://www.occ.gov"
OCC_SEARCH_URL = f"{OCC_BASE}/publications-and-resources/tools/index-cra-search.html"

FDIC_BASE = "https://crapes.fdic.gov"

import os
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".crascraper", "cache")


@dataclass
class CRARating:
    """A single CRA rating record from an examination."""
    bank_id: str
    bank_name: str
    rating: str
    exam_date: str
    public_release_date: Optional[str] = None
    regulator: Optional[str] = None
    exam_method: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    asset_size: Optional[float] = None
    pe_url: Optional[str] = None

    @property
    def rating_score(self) -> Optional[int]:
        return RATING_SCORES.get(self.rating)

    @property
    def is_passing(self) -> bool:
        return self.rating in ("Outstanding", "Satisfactory")

    @property
    def needs_attention(self) -> bool:
        return self.rating in ("Needs to Improve", "Substantial Noncompliance")

    @property
    def asset_size_mm(self) -> Optional[float]:
        if self.asset_size:
            return self.asset_size / 1_000_000
        return None

    def __repr__(self):
        return (
            f"CRARating({self.bank_name!r}, {self.rating!r}, "
            f"exam_date={self.exam_date!r})"
        )


@dataclass
class BankRatingHistory:
    """Complete rating history for a single bank."""
    bank_id: str
    bank_name: str
    ratings: list = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.ratings)

    @property
    def latest_rating(self) -> Optional[CRARating]:
        if not self.ratings:
            return None
        return max(self.ratings, key=lambda r: r.exam_date)

    @property
    def trend(self) -> Optional[str]:
        if len(self.ratings) < 2:
            return None
        sorted_ratings = sorted(self.ratings, key=lambda r: r.exam_date)
        scores = [r.rating_score for r in sorted_ratings if r.rating_score]
        if len(scores) < 2:
            return None
        if scores[-1] > scores[-2]:
            return "improving"
        elif scores[-1] < scores[-2]:
            return "declining"
        return "stable"

    @property
    def has_downgrade(self) -> bool:
        if len(self.ratings) < 2:
            return False
        sorted_ratings = sorted(self.ratings, key=lambda r: r.exam_date)
        scores = [r.rating_score for r in sorted_ratings if r.rating_score]
        for i in range(1, len(scores)):
            if scores[i] < scores[i-1]:
                return True
        return False


@dataclass
class PerformanceEvaluation:
    """Parsed content from a CRA Performance Evaluation PDF."""
    bank_id: str
    bank_name: str
    exam_date: str
    overall_rating: str
    regulator: str
    assessment_areas: list = field(default_factory=list)
    lending_test_rating: Optional[str] = None
    investment_test_rating: Optional[str] = None
    service_test_rating: Optional[str] = None
    community_development_rating: Optional[str] = None
    total_loans: Optional[float] = None
    cd_loans: Optional[float] = None
    cd_investments: Optional[float] = None
    pe_url: Optional[str] = None
    raw_text: Optional[str] = None
