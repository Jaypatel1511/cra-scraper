import pytest
import requests

from crascraper.scrapers.ffiec import _sample_ratings, search_ratings
from crascraper.exceptions import (
    CRAScraperError, FFIECAccessError, FFIECParseError,
)


# --- Fabricated bank names from _sample_ratings(): used to PROVE that no failure
# path ever leaks this data back to a caller as if it were real. ---------------
_FABRICATED_NAMES = {
    "Broadway Federal Bank", "Carver Federal Savings Bank",
    "Sample Community Bank", "Heritage Trust Bank",
    "Pacific Western Federal", "Southern Community CDFI Bank",
}

# --- Minimal HTML fixtures (no network) ---------------------------------------
_SEARCH_PAGE = """
<html><body>
  <input type="hidden" name="__VIEWSTATE" value="abc" />
  <input type="hidden" name="__VIEWSTATEGENERATOR" value="gen" />
  <input type="hidden" name="__EVENTVALIDATION" value="val" />
</body></html>
"""

_RESULTS_WITH_ONE_ROW = """
<html><body>
  <table id="GridView1">
    <tr><th>ID</th><th>Name</th><th>City</th><th>State</th><th>Rating</th><th>Exam</th><th>Method</th></tr>
    <tr><td>99001</td><td>Realdata National Bank</td><td>Austin</td><td>TX</td><td>Satisfactory</td><td>2022-05-01</td><td>Large Bank</td></tr>
  </table>
</body></html>
"""

_RESULTS_EMPTY_TABLE = """
<html><body>
  <table id="GridView1">
    <tr><th>ID</th><th>Name</th><th>City</th><th>State</th><th>Rating</th><th>Exam</th><th>Method</th></tr>
  </table>
</body></html>
"""

# A genuine results page that reached us but rendered NO rows table at all (an
# empty ASP.NET GridView can emit no <table>). The results-page markers (title
# heading + form action + empty-result message) are present, so this is a VALID
# zero-result search and must return [] — NOT a parse error.
_RESULTS_PAGE_NO_TABLE = """
<html><head><title>Institution Rating Search Results</title></head>
<body>
  <form action="InstitutionRatingsSearchResults.aspx" method="post">
    <div id="content">No institutions matched your search criteria.</div>
  </form>
</body></html>
"""

_PAGE_NO_TABLE = "<html><body><h1>Service unavailable</h1></body></html>"

# A 200 error/maintenance page that merely CONTAINS an empty-result-like phrase but
# carries NO structural results-page marker (no GridView1 id, no results-form action).
# A text phrase alone must NOT make this count as a valid zero-result: accepting it
# would let an error page masquerade as "search ran, no matches" and return [] — the
# inverse of the no-data==failure confusion this branch eliminates. Must RAISE.
_PAGE_TEXT_ONLY_NO_STRUCTURE = (
    "<html><body><h1>System maintenance</h1>"
    "<p>No records available at this time. Please try again later.</p>"
    "</body></html>"
)


class _FakeResponse:
    def __init__(self, text="", status_code=200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            err = requests.HTTPError(f"{self.status_code} Client Error")
            err.response = self
            raise err


def _install_fake_request(monkeypatch, *, get=None, post=None, raise_exc=None):
    """Patch requests.Session.request with an offline fake. Records calls so a
    test can assert the mock was actually exercised."""
    calls = []

    def _request(self, method, url, **kwargs):
        calls.append((method, url))
        if raise_exc is not None:
            raise raise_exc
        return get if method == "get" else post

    monkeypatch.setattr(requests.Session, "request", _request)
    return calls


# --- _sample_ratings is a labeled demo helper: still valid on its own ----------
def test_sample_ratings_returns_list():
    ratings = _sample_ratings()
    assert isinstance(ratings, list)
    assert len(ratings) > 0


def test_sample_ratings_have_required_fields():
    for r in _sample_ratings():
        assert r.bank_id
        assert r.bank_name
        assert r.rating
        assert r.exam_date


def test_sample_ratings_have_diverse_ratings():
    rating_set = set(r.rating for r in _sample_ratings())
    assert len(rating_set) >= 3


# --- INTEGRITY: 403 must RAISE honestly and NEVER return fabricated data -------
def test_403_raises_honest_access_error_no_fabricated_data(monkeypatch):
    calls = _install_fake_request(
        monkeypatch, get=_FakeResponse(status_code=403),
    )
    with pytest.raises(FFIECAccessError) as exc:
        search_ratings(bank_name="Broadway")

    msg = str(exc.value)
    # Honest, non-reassuring, cause-specific message.
    assert "403" in msg
    assert "Cloudflare" in msg
    assert "residential" in msg
    assert "cloud" in msg.lower()
    # Must NOT tell the user to retry or fix their input.
    assert "try again" not in msg.lower()
    assert "check your input" not in msg.lower()
    # The mock was actually exercised (no accidental real network call).
    assert calls and calls[0][0] == "get"


def test_403_does_not_return_sample_ratings(monkeypatch):
    """The core regression test: the prior bug returned _sample_ratings() on 403."""
    _install_fake_request(monkeypatch, get=_FakeResponse(status_code=403))
    with pytest.raises(FFIECAccessError):
        search_ratings(bank_name="Broadway")
    # If we ever regress to returning data, the raises above would fail first;
    # this test exists to lock the contract in place.


def test_non_403_http_error_raises_access_error(monkeypatch):
    calls = _install_fake_request(monkeypatch, get=_FakeResponse(status_code=500))
    with pytest.raises(FFIECAccessError) as exc:
        search_ratings(bank_name="Broadway")
    msg = str(exc.value)
    assert "500" in msg
    assert "Cloudflare" not in msg  # 500 is not the edge-block story
    assert calls


def test_network_error_raises_access_error(monkeypatch):
    _install_fake_request(
        monkeypatch, raise_exc=requests.ConnectionError("dns failure"),
    )
    with pytest.raises(FFIECAccessError) as exc:
        search_ratings(bank_name="Broadway")
    assert "Could not reach FFIEC" in str(exc.value)


# --- HAPPY PATH: a successful fetch parses to REAL records ---------------------
def test_successful_fetch_parses_real_records(monkeypatch):
    calls = _install_fake_request(
        monkeypatch,
        get=_FakeResponse(_SEARCH_PAGE),
        post=_FakeResponse(_RESULTS_WITH_ONE_ROW),
    )
    results = search_ratings(bank_name="Realdata")
    assert len(results) == 1
    rec = results[0]
    assert rec.bank_id == "99001"
    assert rec.bank_name == "Realdata National Bank"
    assert rec.rating == "Satisfactory"
    # Real records come ONLY from parsed HTML, never from the fabricated set.
    assert rec.bank_name not in _FABRICATED_NAMES
    # Both the GET (viewstate) and POST (form) were made.
    assert [c[0] for c in calls] == ["get", "post"]


# --- BOUNDARY: empty results table is a VALID zero-result, NOT an error --------
def test_empty_results_table_returns_empty_list(monkeypatch):
    _install_fake_request(
        monkeypatch,
        get=_FakeResponse(_SEARCH_PAGE),
        post=_FakeResponse(_RESULTS_EMPTY_TABLE),
    )
    results = search_ratings(bank_name="NoSuchBankXYZ")
    assert results == []  # zero-result search must NOT raise


# --- BOUNDARY: results page reached but NO rows table at all is still a VALID
# zero-result, NOT a parse error. The decision is gated on the results-page
# marker, not on whether any <table> rendered. ---------------------------------
def test_results_page_without_table_returns_empty_list(monkeypatch):
    _install_fake_request(
        monkeypatch,
        get=_FakeResponse(_SEARCH_PAGE),
        post=_FakeResponse(_RESULTS_PAGE_NO_TABLE),
    )
    results = search_ratings(bank_name="NoSuchBankXYZ")
    # Confirmably reached the results page + no rows = valid empty; must NOT raise.
    assert results == []


# --- BOUNDARY: a 200 that is genuinely not a results page is a PARSE error -----
def test_unparseable_page_raises_parse_error(monkeypatch):
    _install_fake_request(
        monkeypatch,
        get=_FakeResponse(_SEARCH_PAGE),
        post=_FakeResponse(_PAGE_NO_TABLE),
    )
    with pytest.raises(FFIECParseError) as exc:
        search_ratings(bank_name="Realdata")
    msg = str(exc.value)
    assert "parse" in msg.lower()
    # Must not be conflated with the access-block story.
    assert "Cloudflare" not in msg


# --- BOUNDARY: a TEXT phrase alone is NOT a results page. A 200 error/maintenance
# page that merely contains an empty-result-like substring ("no records ...") but
# carries NO structural marker (no GridView1 id, no results-form action) must RAISE
# FFIECParseError, NOT be silently treated as a valid zero-result. This is load-
# bearing: the prior text-only acceptance returned [] here. ---------------------
def test_text_only_no_structural_marker_raises_parse_error(monkeypatch):
    _install_fake_request(
        monkeypatch,
        get=_FakeResponse(_SEARCH_PAGE),
        post=_FakeResponse(_PAGE_TEXT_ONLY_NO_STRUCTURE),
    )
    with pytest.raises(FFIECParseError) as exc:
        search_ratings(bank_name="NoSuchBankXYZ")
    msg = str(exc.value)
    assert "parse" in msg.lower()
    # An error page masquerading via text must not be conflated with a zero-result.
    assert "Cloudflare" not in msg


# --- No failure path leaks fabricated data ------------------------------------
@pytest.mark.parametrize("scenario", ["403", "500", "network", "unparseable"])
def test_no_failure_path_returns_fabricated_data(monkeypatch, scenario):
    if scenario == "403":
        _install_fake_request(monkeypatch, get=_FakeResponse(status_code=403))
    elif scenario == "500":
        _install_fake_request(monkeypatch, get=_FakeResponse(status_code=500))
    elif scenario == "network":
        _install_fake_request(monkeypatch, raise_exc=requests.Timeout("slow"))
    else:  # unparseable
        _install_fake_request(
            monkeypatch,
            get=_FakeResponse(_SEARCH_PAGE),
            post=_FakeResponse(_PAGE_NO_TABLE),
        )

    with pytest.raises(CRAScraperError) as exc:
        # Whatever happens, the function must raise — never return rows.
        search_ratings(bank_name="Broadway")

    # ...and the raised error must not leak any fabricated bank name in its text.
    # (The raise itself guarantees no rows were returned; this asserts the message
    # never smuggles the placeholder data back to the caller either.)
    msg = str(exc.value)
    leaked = [name for name in _FABRICATED_NAMES if name in msg]
    assert not leaked, f"fabricated names leaked into error message: {leaked}"
