"""
Analyze CRA rating data for insights and CDFI partnership opportunities.
"""
import pandas as pd
from typing import Optional
from collections import defaultdict

from crascraper.data.schema import (
    CRARating, BankRatingHistory, RATING_SCORES, CRA_RATINGS
)


def to_dataframe(ratings: list) -> pd.DataFrame:
    """Convert a list of CRARating objects to a DataFrame."""
    rows = []
    for r in ratings:
        rows.append({
            "bank_id":             r.bank_id,
            "bank_name":           r.bank_name,
            "rating":              r.rating,
            "rating_score":        r.rating_score,
            "exam_date":           r.exam_date,
            "regulator":           r.regulator,
            "exam_method":         r.exam_method,
            "city":                r.city,
            "state":               r.state,
            "asset_size":          r.asset_size,
            "asset_size_mm":       r.asset_size_mm,
            "is_passing":          r.is_passing,
            "needs_attention":     r.needs_attention,
        })
    return pd.DataFrame(rows)


def rating_distribution(ratings: list) -> pd.DataFrame:
    """
    Compute distribution of ratings across a set of examinations.
    """
    df = to_dataframe(ratings)
    if df.empty:
        return pd.DataFrame()

    counts = df["rating"].value_counts().reset_index()
    counts.columns = ["rating", "count"]
    counts["pct"] = counts["count"] / counts["count"].sum() * 100
    counts = counts.sort_values("count", ascending=False)
    return counts


def rating_by_state(ratings: list) -> pd.DataFrame:
    """
    Aggregate ratings by state.
    """
    df = to_dataframe(ratings)
    if df.empty or "state" not in df.columns:
        return pd.DataFrame()

    result = df.groupby("state").agg(
        total_exams=("rating", "count"),
        avg_score=("rating_score", "mean"),
        outstanding_count=("rating", lambda x: (x == "Outstanding").sum()),
        needs_attention_count=("needs_attention", "sum"),
    ).reset_index()

    result["pct_outstanding"] = (
        result["outstanding_count"] / result["total_exams"] * 100
    ).round(1)
    result["pct_needs_attention"] = (
        result["needs_attention_count"] / result["total_exams"] * 100
    ).round(1)

    return result.sort_values("total_exams", ascending=False)


def rating_by_regulator(ratings: list) -> pd.DataFrame:
    """Aggregate ratings by regulator."""
    df = to_dataframe(ratings)
    if df.empty or "regulator" not in df.columns:
        return pd.DataFrame()

    result = df.groupby("regulator").agg(
        total_exams=("rating", "count"),
        avg_score=("rating_score", "mean"),
        outstanding_count=("rating", lambda x: (x == "Outstanding").sum()),
        needs_attention_count=("needs_attention", "sum"),
    ).reset_index()

    return result.sort_values("total_exams", ascending=False)


def find_partnership_opportunities(
    ratings: list,
    state: str = None,
    min_assets: float = None,
    max_assets: float = None,
) -> pd.DataFrame:
    """
    Identify banks with 'Needs to Improve' or 'Substantial Noncompliance' ratings.
    These banks are under regulatory pressure to demonstrate improved community
    lending — making them prime CDFI partnership targets.

    Args:
        ratings:    List of CRARating objects
        state:      Optional state filter
        min_assets: Minimum asset size filter
        max_assets: Maximum asset size filter

    Returns:
        DataFrame of banks flagged as partnership opportunities
    """
    df = to_dataframe(ratings)
    if df.empty:
        return pd.DataFrame()

    df = df[df["needs_attention"] == True].copy()

    if state:
        df = df[df["state"] == state.upper()]
    if min_assets is not None:
        df = df[df["asset_size"] >= min_assets]
    if max_assets is not None:
        df = df[df["asset_size"] <= max_assets]

    return df.sort_values(
        ["state", "rating_score", "exam_date"],
        ascending=[True, True, False]
    )


def build_history(ratings: list) -> dict:
    """
    Group ratings by bank to build rating histories.
    Returns dict mapping bank_id to BankRatingHistory.
    """
    histories = defaultdict(lambda: BankRatingHistory(bank_id="", bank_name=""))

    for r in ratings:
        if not histories[r.bank_id].bank_id:
            histories[r.bank_id] = BankRatingHistory(
                bank_id=r.bank_id,
                bank_name=r.bank_name,
                ratings=[]
            )
        histories[r.bank_id].ratings.append(r)

    return dict(histories)


def find_downgrades(ratings: list) -> pd.DataFrame:
    """
    Identify banks that have been downgraded between examinations.
    """
    histories = build_history(ratings)

    rows = []
    for bank_id, hist in histories.items():
        if not hist.has_downgrade:
            continue

        sorted_ratings = sorted(hist.ratings, key=lambda r: r.exam_date)
        for i in range(1, len(sorted_ratings)):
            prev = sorted_ratings[i-1]
            curr = sorted_ratings[i]
            if curr.rating_score and prev.rating_score:
                if curr.rating_score < prev.rating_score:
                    rows.append({
                        "bank_id":      bank_id,
                        "bank_name":    hist.bank_name,
                        "prior_rating": prev.rating,
                        "prior_date":   prev.exam_date,
                        "new_rating":   curr.rating,
                        "new_date":     curr.exam_date,
                        "rating_drop": prev.rating_score - curr.rating_score,
                    })

    return pd.DataFrame(rows).sort_values(
        ["rating_drop", "new_date"], ascending=[False, False]
    ) if rows else pd.DataFrame()


def summary_report(ratings: list) -> str:
    """
    Generate a Markdown summary report of CRA rating data.
    """
    df = to_dataframe(ratings)
    if df.empty:
        return "No ratings data available."

    lines = [
        "# CRA Ratings Summary Report",
        "",
        f"**Total Examinations:** {len(df):,}",
        f"**Unique Banks:** {df['bank_id'].nunique():,}",
        f"**States Represented:** {df['state'].nunique() if 'state' in df.columns else 0}",
        f"**Average Rating Score:** {df['rating_score'].mean():.2f} (out of 4.0)",
        "",
        "## Rating Distribution",
        "",
        "| Rating | Count | Percentage |",
        "|--------|-------|------------|",
    ]

    dist = rating_distribution(ratings)
    for _, row in dist.iterrows():
        lines.append(f"| {row['rating']} | {row['count']:,} | {row['pct']:.1f}% |")

    needs_attn = df[df["needs_attention"] == True]
    lines += [
        "",
        f"## Partnership Opportunities ({len(needs_attn)} banks)",
        "",
        "Banks with 'Needs to Improve' or 'Substantial Noncompliance' ratings.",
        "",
    ]

    if len(needs_attn) > 0:
        lines.append("| Bank | Location | Rating | Exam Date | Assets ($MM) |")
        lines.append("|------|----------|--------|-----------|--------------|")
        for _, row in needs_attn.head(20).iterrows():
            assets = f"${row['asset_size_mm']:,.0f}" if pd.notna(row['asset_size_mm']) else "N/A"
            location = f"{row['city'] or '?'}, {row['state'] or '?'}"
            lines.append(
                f"| {row['bank_name']} | {location} | "
                f"{row['rating']} | {row['exam_date']} | {assets} |"
            )

    return "\n".join(lines)
