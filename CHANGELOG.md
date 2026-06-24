# Changelog

All notable changes to cra-scraper are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.1] - 2026-06-24

### Fixed (data integrity)
- **`search_ratings()` no longer fabricates data on failure.** Previously, ANY
  failure (HTTP error, network error, parse error) was caught by a blanket
  `except Exception` that printed a benign message and returned six hardcoded fake
  bank records from `_sample_ratings()` — plausible-looking but entirely fabricated
  CRA ratings, returned to the caller as if they were real, with no error raised.
  This was a silent data-integrity bug: a consumer could not tell fabricated data
  from a real result. `search_ratings()` now **raises** on failure and **never**
  returns sample/placeholder data. `_sample_ratings()` remains available as
  explicitly-labeled demo/test data, but is unreachable from the live fetch path.

### Added
- Typed exception hierarchy (`CRAScraperError`, `FFIECAccessError`,
  `FFIECParseError`), all subclassing `RuntimeError` for backward compatibility.
  Failures now surface an honest, cause-specific message:
  - **HTTP 403** is reported as an FFIEC/Cloudflare edge access block — explicitly
    *not* a code bug, *not* bad input, and *not* transient. Cloudflare blocks
    cloud/datacenter IP ranges (Colab, CI runners, hosted notebooks, most cloud
    VMs); no User-Agent or header change clears it. The workaround is to run from a
    residential connection.
  - Other HTTP/network errors get status-specific honest messages.
  - A successfully-fetched-but-unparseable page raises `FFIECParseError`, kept
    strictly distinct from a legitimate zero-result search (which still returns an
    empty list — an empty results table is a valid result, never an error).

### Changed
- Replaced the browser-mimicking `Mozilla/5.0`-prefixed User-Agent with a clean
  identifying tool-token UA (`cra-scraper/<version> (+repo url)`) plus standard
  `Accept` headers. The browser-prefixed UA was a latent residential-fingerprint
  bug on its own merits; this change does **not** attempt to defeat the 403 (it
  cannot — the block is by IP reputation, not header).

### Scope / honesty note
This release fixes a silent-fabrication bug and makes errors honest. It does **not**
make the scrape succeed from cloud/datacenter environments — those IPs remain blocked
by FFIEC's Cloudflare edge, now reported honestly instead of masked by fake data. The
scrape works from residential connections. No retries, caching, or new data sources
were added (the 403 is deterministic by IP, so retries would not help).

## [0.1.0]

- Initial release — CRA exam ratings scraper, FFIEC search, PE PDF parsing,
  CDFI partnership analysis.
