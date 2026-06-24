"""Single source of truth for the package version.

Kept as a leaf module (no intra-package imports) so it can be imported from
anywhere — including crascraper.scrapers.ffiec — without the circular import
that would result from importing __version__ off the package __init__, which
imports the scrapers before __version__ would be defined.
"""
__version__ = "0.1.1"
