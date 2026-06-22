# pipeline/gold.py

import logging

import pandas as pd

from utils.db import get_engine

engine = get_engine()
# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Gold 1: Ticket KPIs
# ------------------------------------------------------------------

def build_ticket_kpis(df):

    logger.info(
        "Building gold.ticket_kpis"
    )

    kpis = (
        df.groupby(
            ["category_clean", "priority_clean"],
            dropna=False
        )
        .agg(
            ticket_count=("ticket_id", "count"),
            avg_cost=("cost_clean", "mean")
        )
        .reset_index()
    )

    if (
        "created_at" in df.columns
        and "resolved_at" in df.columns
    ):

        df["resolution_hours"] = (
            (
                df["resolved_at"]
                - df["created_at"]
            )
            .dt.total_seconds()
            / 3600
        )

        resolution = (
            df.groupby(
                ["category_clean", "priority_clean"]
            )
            .agg(
                avg_resolution_hours=(
                    "resolution_hours",
                    "mean"
                )
            )
            .reset_index()
        )

        kpis = kpis.merge(
            resolution,
            on=[
                "category_clean",
                "priority_clean"
            ],
            how="left"
        )

    kpis.to_sql(
        "ticket_kpis",
        engine,
        schema="gold",
        if_exists="replace",
        index=False
    )

    logger.info(
        f"gold.ticket_kpis rows: {len(kpis):,}"
    )


# ------------------------------------------------------------------
# Gold 2: Building Hotspots
# ------------------------------------------------------------------

def build_building_hotspots(df):

    logger.info(
        "Building gold.building_hotspots"
    )

    if "building" not in df.columns:
        logger.warning(
            "building column not found"
        )
        return

    hotspots = (
        df.groupby(
            ["building", "category_clean"],
            dropna=False
        )
        .agg(
            ticket_count=("ticket_id", "count"),
            total_cost=("cost_clean", "sum"),
            avg_cost=("cost_clean", "mean")
        )
        .reset_index()
        .sort_values(
            "ticket_count",
            ascending=False
        )
    )

    hotspots.to_sql(
        "building_hotspots",
        engine,
        schema="gold",
        if_exists="replace",
        index=False
    )

    logger.info(
        f"gold.building_hotspots rows: {len(hotspots):,}"
    )


# ------------------------------------------------------------------
# Gold 3: Assignee Performance
# ------------------------------------------------------------------

def build_assignee_performance(df):

    logger.info(
        "Building gold.assignee_performance"
    )

    if "assigned_to" not in df.columns:
        logger.warning(
            "assigned_to column not found"
        )
        return

    assignee = (
        df.groupby(
            "assigned_to",
            dropna=False
        )
        .agg(
            ticket_count=("ticket_id", "count"),
            avg_cost=("cost_clean", "mean")
        )
        .reset_index()
    )

    if (
        "created_at" in df.columns
        and "resolved_at" in df.columns
    ):

        df["resolution_hours"] = (
            (
                df["resolved_at"]
                - df["created_at"]
            )
            .dt.total_seconds()
            / 3600
        )

        resolution = (
            df.groupby("assigned_to")
            .agg(
                avg_resolution_hours=(
                    "resolution_hours",
                    "mean"
                )
            )
            .reset_index()
        )

        assignee = assignee.merge(
            resolution,
            on="assigned_to",
            how="left"
        )

    assignee.to_sql(
        "assignee_performance",
        engine,
        schema="gold",
        if_exists="replace",
        index=False
    )

    logger.info(
        f"gold.assignee_performance rows: {len(assignee):,}"
    )


# ------------------------------------------------------------------
# Main Gold Build
# ------------------------------------------------------------------

def build_gold():

    logger.info(
        "Starting Gold Layer Build"
    )

    try:

        df = pd.read_sql(
            """
            SELECT *
            FROM silver.tickets
            """,
            engine
        )

        logger.info(
            f"Loaded {len(df):,} rows from silver.tickets"
        )

        build_ticket_kpis(df.copy())

        build_building_hotspots(df.copy())

        build_assignee_performance(df.copy())

        logger.info(
            "Gold Layer Build Completed"
        )

    except Exception as e:

        logger.exception(
            f"Gold Layer Failed: {str(e)}"
        )

        raise


# ------------------------------------------------------------------
# Entry Point
# ------------------------------------------------------------------

if __name__ == "__main__":
    build_gold()