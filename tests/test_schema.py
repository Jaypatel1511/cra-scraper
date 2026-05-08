import pytest
from crascraper.data.schema import CRARating, BankRatingHistory, RATING_SCORES


def test_rating_created(sample_rating):
    assert sample_rating.bank_name == "Broadway Federal Bank"
    assert sample_rating.rating == "Outstanding"


def test_rating_score(sample_rating):
    assert sample_rating.rating_score == 4


def test_is_passing(sample_rating):
    assert sample_rating.is_passing == True


def test_needs_attention_outstanding(sample_rating):
    assert sample_rating.needs_attention == False


def test_needs_attention_low_rating():
    rating = CRARating(
        bank_id="X", bank_name="X", rating="Needs to Improve",
        exam_date="2024-01-01"
    )
    assert rating.needs_attention == True


def test_asset_size_mm(sample_rating):
    assert sample_rating.asset_size_mm == 655.0


def test_history_count(history_ratings):
    hist = BankRatingHistory(
        bank_id="55555", bank_name="Sample Trust Bank",
        ratings=history_ratings
    )
    assert hist.count == 3


def test_history_latest(history_ratings):
    hist = BankRatingHistory(
        bank_id="55555", bank_name="Sample Trust Bank",
        ratings=history_ratings
    )
    assert hist.latest_rating.rating == "Needs to Improve"


def test_history_trend(history_ratings):
    hist = BankRatingHistory(
        bank_id="55555", bank_name="Sample Trust Bank",
        ratings=history_ratings
    )
    assert hist.trend == "declining"


def test_history_has_downgrade(history_ratings):
    hist = BankRatingHistory(
        bank_id="55555", bank_name="Sample Trust Bank",
        ratings=history_ratings
    )
    assert hist.has_downgrade == True
