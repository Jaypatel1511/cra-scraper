import pytest
from crascraper.scrapers.ffiec import _sample_ratings, search_ratings


def test_sample_ratings_returns_list():
    ratings = _sample_ratings()
    assert isinstance(ratings, list)
    assert len(ratings) > 0


def test_sample_ratings_have_required_fields():
    ratings = _sample_ratings()
    for r in ratings:
        assert r.bank_id
        assert r.bank_name
        assert r.rating
        assert r.exam_date


def test_sample_ratings_have_diverse_ratings():
    ratings = _sample_ratings()
    rating_set = set(r.rating for r in ratings)
    assert len(rating_set) >= 3


def test_search_returns_list_or_empty():
    """Network test — falls back to sample data on failure."""
    results = search_ratings(bank_name="Broadway")
    assert isinstance(results, list)
