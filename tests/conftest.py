import pytest
from crascraper.data.schema import CRARating
from crascraper.scrapers.ffiec import _sample_ratings


@pytest.fixture
def sample_ratings():
    return _sample_ratings()


@pytest.fixture
def sample_rating():
    return CRARating(
        bank_id="57542",
        bank_name="Broadway Federal Bank",
        rating="Outstanding",
        exam_date="2023-08-15",
        regulator="OCC",
        exam_method="Large Bank",
        city="Los Angeles",
        state="CA",
        asset_size=655_000_000,
    )


@pytest.fixture
def history_ratings():
    """Multiple exams for the same bank to test history."""
    return [
        CRARating(
            bank_id="55555",
            bank_name="Sample Trust Bank",
            rating="Outstanding",
            exam_date="2018-06-01",
            asset_size=300_000_000,
        ),
        CRARating(
            bank_id="55555",
            bank_name="Sample Trust Bank",
            rating="Satisfactory",
            exam_date="2021-06-15",
            asset_size=350_000_000,
        ),
        CRARating(
            bank_id="55555",
            bank_name="Sample Trust Bank",
            rating="Needs to Improve",
            exam_date="2024-04-20",
            asset_size=400_000_000,
        ),
    ]
