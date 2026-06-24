"""Typed exceptions for cra-scraper.

These inherit from RuntimeError for backward compatibility: callers that
previously caught broad RuntimeError/Exception keep working, while new callers
can catch the specific type. This mirrors the wider portfolio convention
(e.g. hmda-analyzer's CFPBAPIError, cdfi-benchmark's FDICAPIError).
"""


class CRAScraperError(RuntimeError):
    """Base class for all cra-scraper errors."""


class FFIECAccessError(CRAScraperError):
    """Raised when the FFIEC site could not be reached or returned an HTTP error.

    This means NO data was retrieved. It is NOT a parse problem and it is NOT a
    zero-result search. The most common cause from cloud/datacenter environments
    is an FFIEC/Cloudflare edge access block (see search_ratings for the message).
    """


class FFIECParseError(CRAScraperError):
    """Raised when a page WAS fetched successfully (HTTP 200) but its content is
    not a recognizable FFIEC results page and cannot be parsed.

    This is distinct from a legitimate zero-result search: a successful fetch of a
    valid results page that simply contains no matching rows returns an empty list,
    NOT this error. Conflating "no matches" with "could not parse" would reintroduce
    a signal-confusion bug, so the two are kept strictly separate.
    """
