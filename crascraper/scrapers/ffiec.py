"""
Scrape CRA rating data from FFIEC public ratings database.
"""
import requests
from typing import Optional
from bs4 import BeautifulSoup

from crascraper._version import __version__
from crascraper.data.schema import (
    CRARating, FFIEC_SEARCH_URL, FFIEC_RESULTS_URL,
)
from crascraper.exceptions import FFIECAccessError, FFIECParseError


# A clean, identifying tool-token User-Agent. This deliberately does NOT mimic a
# browser: a browser-prefixed UA is a latent residential-fingerprint bug, and it
# does NOT help with the FFIEC/Cloudflare edge block from cloud IPs anyway (that
# block is by IP reputation, not by header). Identify honestly instead.
HEADERS = {
    "User-Agent": f"cra-scraper/{__version__} (+https://github.com/Jaypatel1511/cra-scraper)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
TIMEOUT = 30


def search_ratings(
    bank_name: str = None,
    bank_id: str = None,
    state: str = None,
    rating: str = None,
    exam_date_from: str = None,
    exam_date_to: str = None,
    limit: int = 100,
) -> list:
    """
    Search FFIEC CRA ratings database.

    Args:
        bank_name:     Bank name (partial match)
        bank_id:       FDIC certificate or OCC charter number
        state:         Two-letter state code
        rating:        Filter by rating (Outstanding, Satisfactory, etc.)
        exam_date_from: Exam date lower bound (YYYY-MM-DD)
        exam_date_to:   Exam date upper bound (YYYY-MM-DD)
        limit:         Max results

    Returns:
        List of CRARating objects. An empty list is a VALID result meaning the
        search ran successfully but matched no banks — it never means "blocked".

    Raises:
        FFIECAccessError: the site could not be reached or returned an HTTP error
            (no data was retrieved). On HTTP 403 this is almost always an
            FFIEC/Cloudflare edge access block — see the message.
        FFIECParseError: a page was fetched successfully but is not a recognizable
            FFIEC results page and could not be parsed.

    This function NEVER returns fabricated/sample data. On any failure it raises;
    it does not silently substitute placeholder records. (Prior versions returned
    six hardcoded fake bank records on any error — that integrity bug is fixed.)
    """
    # FFIEC uses ASP.NET viewstate-based forms, which require fetching the search
    # page first to obtain hidden state tokens.
    session = requests.Session()
    session.headers.update(HEADERS)

    r = _fetch(session, "get", FFIEC_SEARCH_URL)

    soup = BeautifulSoup(r.text, "html.parser")
    viewstate = _get_input_value(soup, "__VIEWSTATE")
    viewstategen = _get_input_value(soup, "__VIEWSTATEGENERATOR")
    eventvalidation = _get_input_value(soup, "__EVENTVALIDATION")

    form_data = {
        "__VIEWSTATE":          viewstate or "",
        "__VIEWSTATEGENERATOR": viewstategen or "",
        "__EVENTVALIDATION":    eventvalidation or "",
    }
    if bank_name:
        form_data["txtBankName"] = bank_name
    if bank_id:
        form_data["txtIDNumber"] = str(bank_id)
    if state:
        form_data["ddlState"] = state.upper()

    r = _fetch(session, "post", FFIEC_RESULTS_URL, data=form_data)

    return _parse_results_html(r.text, limit=limit)


def _fetch(session: requests.Session, method: str, url: str, **kwargs):
    """Perform an HTTP request and raise an honest, typed FFIECAccessError on any
    network failure or non-2xx status. Never swallows; never returns fake data."""
    try:
        r = session.request(method, url, timeout=TIMEOUT, **kwargs)
        r.raise_for_status()
        return r
    except requests.HTTPError as e:
        status = getattr(e.response, "status_code", None)
        raise FFIECAccessError(_access_error_message(status, url, e)) from e
    except requests.RequestException as e:
        raise FFIECAccessError(
            f"Could not reach FFIEC at {url}: {e}. This is a network/connection "
            f"failure (no data was retrieved), not a parsing problem and not a "
            f"zero-result search."
        ) from e


def _access_error_message(status: Optional[int], url: str, err: Exception) -> str:
    """Build an honest, cause-specific message. The 403 case is deliberately
    non-reassuring: it is an IP-reputation / edge block, not something the caller
    can fix by retrying or correcting input."""
    if status == 403:
        return (
            f"FFIEC returned HTTP 403 (Forbidden) for {url}. This is an "
            f"FFIEC/Cloudflare edge access block. It is NOT a bug in this library, "
            f"NOT a problem with your search input, and NOT transient — Cloudflare "
            f"blocks requests from cloud/datacenter IP ranges (Google Colab, CI "
            f"runners, hosted notebooks, most cloud VMs). No User-Agent, header "
            f"change, or retry will clear it. The scrape works from a residential "
            f"internet connection; run it from one to obtain the data."
        )
    if status is not None:
        return (
            f"FFIEC returned HTTP {status} for {url}: {err}. No data was retrieved. "
            f"This is an access/server error, not a parsing problem and not a "
            f"zero-result search."
        )
    return (
        f"FFIEC request to {url} failed: {err}. No data was retrieved."
    )


def _get_input_value(soup: BeautifulSoup, name: str) -> Optional[str]:
    """Get the value of a hidden input field."""
    el = soup.find("input", {"name": name})
    if el:
        return el.get("value", "")
    return None


def _is_results_page(soup: BeautifulSoup) -> bool:
    """True if the parsed HTML is recognizably the FFIEC results page, whether or
    not the results grid contains any rows.

    Acceptance is gated on a STRUCTURAL marker only — never on page text alone.
    A bare empty-result phrase ("no records", "no institutions matched", ...) can
    appear on an error/maintenance page that happens to be served with HTTP 200;
    accepting on text alone would let such a page masquerade as a valid zero-result
    and return [] silently — the same "no data == failure" confusion this module
    exists to eliminate, merely inverted. So a results page is recognized ONLY by:
      1. an element carrying the results grid id ``GridView1`` — present in the
         typical rendering even when the grid has only a header / no data rows; or
      2. a ``<form>`` whose action targets the results page
         (``InstitutionRatingsSearchResults.aspx``) — present on every postback
         render of that page, rows or not.
    These are deliberately NOT "some <table> exists": an empty ASP.NET GridView can
    render no <table> at all, yet a legitimate zero-match search must still return
    [] (not raise). Both structural markers were verified to reject Cloudflare/
    error/JS-shell pages. Either one confirms we reached the results page.
    """
    if soup.find(id="GridView1"):
        return True
    form = soup.find("form")
    if form and "InstitutionRatingsSearchResults" in (form.get("action") or ""):
        return True
    return False


def _parse_results_html(html: str, limit: int = 100) -> list:
    """Parse the FFIEC results page HTML.

    Boundary (important — do not conflate the two signals):
      * If we confirmably reached the results page (see ``_is_results_page``) but
        the rows grid is absent or contains no data rows, this is a VALID
        zero-result search and returns an empty list. A legitimate "no matches"
        must NEVER raise — even if the empty page renders without a <table> at all.
      * If the page carries NONE of the results-page markers, the fetched page is
        not a recognizable FFIEC results page (e.g. an error/maintenance/redirect
        page or a JS-only shell), and FFIECParseError is raised.

    The empty-vs-error distinction is gated on a results-page MARKER, not on the
    mere presence of any <table>, so a genuine zero-result is never misclassified
    as a parse error regardless of how the empty page happens to render.
    """
    soup = BeautifulSoup(html, "html.parser")

    if not _is_results_page(soup):
        raise FFIECParseError(
            "Fetched a page from FFIEC (HTTP 200) but it carries none of the "
            "FFIEC results-page markers; the page does not look like an FFIEC "
            "results page. This is a parse failure, NOT a zero-result search and "
            "NOT an access block."
        )

    # We reached the results page. Locate the rows grid; if it is absent or has no
    # data rows, that is a legitimate zero-result search -> [].
    table = soup.find("table", {"id": "GridView1"}) or soup.find("table")
    if table is None:
        return []

    ratings = []
    rows = table.find_all("tr")[1:]  # skip header

    for row in rows[:limit]:
        cells = row.find_all("td")
        if len(cells) < 5:
            continue

        try:
            ratings.append(CRARating(
                bank_id=cells[0].get_text(strip=True),
                bank_name=cells[1].get_text(strip=True),
                city=cells[2].get_text(strip=True) if len(cells) > 2 else None,
                state=cells[3].get_text(strip=True) if len(cells) > 3 else None,
                rating=cells[4].get_text(strip=True) if len(cells) > 4 else "Unknown",
                exam_date=cells[5].get_text(strip=True) if len(cells) > 5 else "",
                exam_method=cells[6].get_text(strip=True) if len(cells) > 6 else None,
            ))
        except Exception:
            continue

    return ratings


def _sample_ratings() -> list:
    """Hand-written sample CRA ratings for tests, demos, and the example notebook.

    WARNING: this is fabricated illustrative data, NOT real CRA ratings. It is
    module-private and is intentionally NEVER returned by search_ratings() or any
    live fetch path — callers reach it only by importing it directly and knowingly
    (e.g. tests/conftest.py and examples/cra_ratings_demo.ipynb). It must never be
    used as a silent fallback for a failed scrape.
    """
    return [
        CRARating(
            bank_id="57542",
            bank_name="Broadway Federal Bank",
            rating="Outstanding",
            exam_date="2023-08-15",
            regulator="OCC",
            exam_method="Large Bank",
            city="Los Angeles",
            state="CA",
            asset_size=655_000_000,
        ),
        CRARating(
            bank_id="33764",
            bank_name="Carver Federal Savings Bank",
            rating="Satisfactory",
            exam_date="2023-04-10",
            regulator="OCC",
            exam_method="Intermediate Small Bank",
            city="New York",
            state="NY",
            asset_size=780_000_000,
        ),
        CRARating(
            bank_id="12345",
            bank_name="Sample Community Bank",
            rating="Needs to Improve",
            exam_date="2024-02-20",
            regulator="FDIC",
            exam_method="Small Bank",
            city="Chicago",
            state="IL",
            asset_size=250_000_000,
        ),
        CRARating(
            bank_id="98765",
            bank_name="Heritage Trust Bank",
            rating="Substantial Noncompliance",
            exam_date="2024-01-15",
            regulator="FDIC",
            exam_method="Small Bank",
            city="Detroit",
            state="MI",
            asset_size=180_000_000,
        ),
        CRARating(
            bank_id="55512",
            bank_name="Pacific Western Federal",
            rating="Outstanding",
            exam_date="2024-03-01",
            regulator="FRS",
            exam_method="Large Bank",
            city="Seattle",
            state="WA",
            asset_size=2_400_000_000,
        ),
        CRARating(
            bank_id="22334",
            bank_name="Southern Community CDFI Bank",
            rating="Outstanding",
            exam_date="2023-11-12",
            regulator="FDIC",
            exam_method="Intermediate Small Bank",
            city="Atlanta",
            state="GA",
            asset_size=420_000_000,
        ),
    ]
