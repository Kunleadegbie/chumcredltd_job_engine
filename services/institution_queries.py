"""
TalentIQ — Institutional Analytics Queries
"""

import os
from supabase import create_client
import pandas as pd

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# =========================
# FETCH ALL SCORES (by institution later)
# =========================

def fetch_institution_scores(
    institution_id: str,
    limit: int = 5000,
):
    """
    Fetch candidate scoring data for ONE institution
    """

    res = (
        supabase
        .table("candidate_scores")
        .select("*")
        .eq("institution_id", institution_id)
        .limit(limit)
        .execute()
    )

    data = res.data or []

    if not data:
        return pd.DataFrame()

    return pd.DataFrame(data)

# =========================
# KPI COMPUTATION
# =========================

def compute_institution_kpis(df: pd.DataFrame):
    if df.empty:
        return None

    kpis = {}

    kpis["avg_cv_quality"] = round(df["cv_quality_score"].mean(), 1)
    kpis["avg_ers"] = round(df["ers_score"].mean(), 1)
    kpis["avg_trust"] = round(df["trust_index"].mean(), 1)

    kpis["employer_ready_pct"] = round(
        (df["trust_badge"] == "Gold").mean() * 100, 1
    )

    kpis["needs_improvement_pct"] = round(
        (df["trust_badge"] == "Developing").mean() * 100, 1
    )

    kpis["evidence_strength_avg"] = round(
        df["evidence_score"].mean(), 1
    )

    return kpis


# =========================
# BADGE DISTRIBUTION
# =========================

def compute_badge_distribution(df: pd.DataFrame):
    if df.empty:
        return None

    dist = (
        df["trust_badge"]
        .value_counts(normalize=True)
        .mul(100)
        .round(1)
        .to_dict()
    )

    return dist

def compute_faculty_performance(df: pd.DataFrame):
    """
    Returns faculty-level intelligence
    """

    if df.empty or "faculty" not in df.columns:
        return pd.DataFrame()

    grouped = (
        df.groupby("faculty")
        .agg(
            students=("user_id", "count"),
            avg_cv_quality=("cv_quality_score", "mean"),
            avg_ers=("ers_score", "mean"),
            avg_trust=("trust_index", "mean"),
            employer_ready_pct=("trust_badge", lambda x: (x == "Gold").mean() * 100),
        )
        .reset_index()
    )

    # round nicely
    numeric_cols = [
        "avg_cv_quality",
        "avg_ers",
        "avg_trust",
        "employer_ready_pct",
    ]

    for col in numeric_cols:
        grouped[col] = grouped[col].round(1)

    return grouped.sort_values("avg_trust", ascending=False)


def fetch_skill_supply(institution_id: str):
    """
    Aggregate skills from students.
    Assumes users table contains skills array or text.
    Adjust field name if needed.
    """

    res = (
        supabase
        .table("users")
        .select("institution_id, faculty, skills")
        .eq("institution_id", institution_id)
        .execute()
    )

    data = res.data or []

    if not data:
        return pd.DataFrame()

    rows = []

    for r in data:
        skills = r.get("skills") or []
        faculty = r.get("faculty") or "Unknown"

        # handle comma text or list
        if isinstance(skills, str):
            skills = [s.strip().lower() for s in skills.split(",")]

        for skill in skills:
            rows.append({
                "faculty": faculty,
                "skill": skill.lower(),
                "supply_count": 1,
            })

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    return (
        df.groupby(["faculty", "skill"])["supply_count"]
        .sum()
        .reset_index()
    )


def fetch_skill_demand(institution_id: str):
    """
    Employer demand signals
    """

    res = (
        supabase
        .table("job_skill_demand")
        .select("institution_id, skill, demand_count")
        .eq("institution_id", institution_id)
        .execute()
    )

    data = res.data or []

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    return (
        df.groupby("skill")["demand_count"]
        .sum()
        .reset_index()
    )


def compute_skill_gap_matrix(supply_df, demand_df):
    """
    Merge supply vs demand and compute gap
    """

    if supply_df.empty or demand_df.empty:
        return pd.DataFrame()

    merged = supply_df.merge(
        demand_df,
        on="skill",
        how="outer"
    ).fillna(0)

    merged["gap"] = merged["demand_count"] - merged["supply_count"]

    return merged


def build_faculty_heatmap(gap_df: pd.DataFrame):
    """
    Pivot for heatmap
    """

    if gap_df.empty:
        return pd.DataFrame()

    pivot = gap_df.pivot_table(
        index="faculty",
        columns="skill",
        values="gap",
        aggfunc="sum",
        fill_value=0,
    )

    return pivot