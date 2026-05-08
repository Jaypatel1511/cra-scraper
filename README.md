# cra-scraper 🏛️

**CRA exam ratings scraper and analyzer.**

Search the FFIEC CRA ratings database programmatically, parse Performance Evaluation
PDFs from OCC, FDIC, and Federal Reserve, and identify banks that are prime CDFI
partnership opportunities — using free public data from federal regulators.

---

## Why cra-scraper?

The Community Reinvestment Act has been law for nearly 50 years and federal regulators
publish exam results for every bank — but there's no programmatic way to access this
data. Banks, CDFIs, fair lending researchers, and journalists all rely on manual PDF
downloads from three different regulator websites. cra-scraper makes CRA exam data
queryable in Python for the first time.

---

## Installation

    pip install cra-scraper

    # For PE PDF parsing
    pip install cra-scraper[pdf]

---

## Quickstart

    from crascraper import (
        search_ratings, find_partnership_opportunities,
        rating_distribution, build_history, find_downgrades,
        summary_report,
    )

    # Search FFIEC ratings (or use sample data when offline)
    ratings = search_ratings(bank_name="Federal")

    # Compute rating distribution
    dist = rating_distribution(ratings)
    print(dist)

    # Find banks with low ratings — CDFI partnership opportunities
    opps = find_partnership_opportunities(ratings, state="IL")
    print(opps)

    # Track rating history per bank
    histories = build_history(ratings)
    for bank_id, hist in histories.items():
        print(f"{hist.bank_name}: {hist.trend}")

    # Identify downgrades
    downgrades = find_downgrades(ratings)
    print(downgrades)

    # Generate a full Markdown summary report
    report = summary_report(ratings)
    print(report)

---

## Parse Performance Evaluation PDFs

    from crascraper import parse_pe_pdf

    pe = parse_pe_pdf("/path/to/performance_eval.pdf")
    print(pe.bank_name)
    print(pe.overall_rating)
    print(pe.lending_test_rating)
    print(pe.assessment_areas)

---

## CRA Rating Categories

| Rating | Score | Meaning |
|--------|-------|---------|
| Outstanding | 4 | Strong CRA performance |
| Satisfactory | 3 | Adequate CRA performance |
| Needs to Improve | 2 | Weak CRA performance |
| Substantial Noncompliance | 1 | Inadequate CRA performance |

---

## Federal Regulators Covered

- **OCC** — Office of the Comptroller of the Currency (national banks)
- **FRS** — Federal Reserve System (state member banks)
- **FDIC** — Federal Deposit Insurance Corporation (state non-member banks)

---

## Use Cases

- **CDFIs** identifying bank partnership opportunities (banks under regulatory pressure to improve community lending)
- **Banks** benchmarking their CRA performance against peers
- **Researchers** studying CRA effectiveness and rating trends over time
- **Journalists** investigating bank performance in low-income communities
- **Regulators** analyzing exam outcomes across asset sizes and regions

---

## Data Sources

- FFIEC CRA Ratings Database — ffiec.gov/craratings
- OCC CRA Search — occ.gov
- FDIC CRAPES — crapes.fdic.gov
- Federal Reserve CRA — federalreserve.gov

All free public data — no API keys required.

---

## Running Tests

    PYTHONPATH=. pytest tests/ -v

28 tests across all modules.

---

## License

MIT 2026 Jaypatel1511
