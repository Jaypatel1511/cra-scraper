import pytest
import pandas as pd
from crascraper.analysis.insights import (
    to_dataframe, rating_distribution, rating_by_state,
    rating_by_regulator, find_partnership_opportunities,
    build_history, find_downgrades, summary_report,
)


def test_to_dataframe(sample_ratings):
    df = to_dataframe(sample_ratings)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == len(sample_ratings)
    assert "rating" in df.columns
    assert "rating_score" in df.columns


def test_rating_distribution(sample_ratings):
    dist = rating_distribution(sample_ratings)
    assert isinstance(dist, pd.DataFrame)
    assert "rating" in dist.columns
    assert "count" in dist.columns
    assert dist["count"].sum() == len(sample_ratings)


def test_rating_by_state(sample_ratings):
    result = rating_by_state(sample_ratings)
    assert isinstance(result, pd.DataFrame)
    if len(result) > 0:
        assert "state" in result.columns
        assert "avg_score" in result.columns


def test_rating_by_regulator(sample_ratings):
    result = rating_by_regulator(sample_ratings)
    assert isinstance(result, pd.DataFrame)
    if len(result) > 0:
        assert "regulator" in result.columns


def test_find_partnership_opportunities(sample_ratings):
    opps = find_partnership_opportunities(sample_ratings)
    assert isinstance(opps, pd.DataFrame)
    if len(opps) > 0:
        assert all(opps["needs_attention"] == True)


def test_build_history(sample_ratings):
    histories = build_history(sample_ratings)
    assert isinstance(histories, dict)
    assert len(histories) > 0


def test_find_downgrades(history_ratings):
    downgrades = find_downgrades(history_ratings)
    assert isinstance(downgrades, pd.DataFrame)
    assert len(downgrades) >= 1


def test_summary_report(sample_ratings):
    report = summary_report(sample_ratings)
    assert isinstance(report, str)
    assert "CRA Ratings Summary Report" in report
    assert "Rating Distribution" in report
