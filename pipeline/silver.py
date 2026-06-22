# pipeline/silver.py

import logging

import pandas as pd
from dateutil import parser
from sqlalchemy import text

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
# Normalization Maps
# ------------------------------------------------------------------

PRIORITY_MAP = {
    "crit": "critical",
    "critical": "critical",
    "urgent!!!": "critical",

    "high": "high",
    "hi": "high",

    "med": "medium",
    "medium": "medium",
    "normal": "medium",

    "low": "low",
    "lo": "low"
}


CATEGORY_MAP = {
    "a/c": "HVAC",
    "hvac": "HVAC",
    "heating/cooling": "HVAC",
    "climate control": "HVAC",

    "elec": "Electrical",
    "electrical systems": "Electrical",
    "power issue": "Electrical",

    "lift": "Elevator",
    "vertical transport": "Elevator",
    "elevator/escalator": "Elevator"
}


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def get_latest_batch_id():
    """
    Returns latest bronze batch id.
    """

    query = """
    SELECT batch_id
    FROM bronze.tickets_raw
    ORDER BY ingested_at DESC
    LIMIT 1
    """

    with engine.connect() as conn:
        return conn.execute(
            text(query)
        ).scalar()


def parse_date(value):
    """
    Parse:
    - ISO dates
    - MM/DD/YYYY
    - DD-Mon-YYYY
    - Unix epoch
    """

    if pd.isna(value):
        return None

    try:
        return parser.parse(str(value))
    except Exception:
        pass

    try:
        return pd.to_datetime(
            int(value),
            unit="s"
        )
    except Exception:
        return None


def clean_cost(value):
    """
    Examples:
    $1234.50 -> 1234.50
    TBD -> NULL
    N/A -> NULL
    -1 -> NULL
    """

    if pd.isna(value):
        return None

    value = str(value).strip()

    value = value.replace("$", "")
    value = value.replace(",", "")

    if value.upper() in [
        "N/A",
        "TBD",
        "NULL",
        "NONE"
    ]:
        return None

    try:

        cost = float(value)

        if cost < 0:
            return None

        return cost

    except Exception:
        return None


def create_quality_flags(row):

    flags = []

    if (
        pd.notna(row.get("created_at"))
        and pd.notna(row.get("resolved_at"))
        and row["resolved_at"] < row["created_at"]
    ):
        flags.append(
            "resolved_before_created"
        )

    if pd.isna(row.get("assigned_to")):
        flags.append(
            "missing_assignee"
        )

    if pd.isna(row.get("ticket_id")):
        flags.append(
            "missing_ticket_id"
        )

    if (
        pd.notna(row.get("cost_clean"))
        and row["cost_clean"] > 50000
    ):
        flags.append(
            "cost_outlier"
        )

    return flags


# ------------------------------------------------------------------
# Main Silver Transformation
# ------------------------------------------------------------------

def build_silver():

    logger.info(
        "Starting Silver Layer Build"
    )

    try:

        # ----------------------------------------------------------
        # Find Latest Bronze Batch
        # ----------------------------------------------------------

        logger.info(
            "Identifying latest bronze batch"
        )

        latest_batch_id = (
            get_latest_batch_id()
        )

        if not latest_batch_id:
            raise Exception(
                "No bronze batches found"
            )

        logger.info(
            f"Latest Bronze Batch: {latest_batch_id}"
        )

        # ----------------------------------------------------------
        # Read Latest Bronze Batch
        # ----------------------------------------------------------

        query = f"""
        SELECT *
        FROM bronze.tickets_raw
        WHERE batch_id = '{latest_batch_id}'
        """

        logger.info(
            "Reading latest bronze batch"
        )

        df = pd.read_sql(
            query,
            engine
        )

        initial_rows = len(df)

        logger.info(
            f"Loaded {initial_rows:,} rows"
        )

        # ----------------------------------------------------------
        # Add Silver Lineage
        # ----------------------------------------------------------

        df["silver_batch_id"] = (
            latest_batch_id
        )

        df["silver_processed_at"] = (
            pd.Timestamp.utcnow()
        )

        # ----------------------------------------------------------
        # Parse Dates
        # ----------------------------------------------------------

        logger.info(
            "Parsing date columns"
        )

        if "created_at" in df.columns:
            df["created_at"] = (
                df["created_at"]
                .apply(parse_date)
            )

        if "resolved_at" in df.columns:
            df["resolved_at"] = (
                df["resolved_at"]
                .apply(parse_date)
            )

        # ----------------------------------------------------------
        # Normalize Priority
        # ----------------------------------------------------------

        logger.info(
            "Normalizing priorities"
        )

        if "priority" in df.columns:

            df["priority_clean"] = (
                df["priority"]
                .astype(str)
                .str.strip()
                .str.lower()
                .map(PRIORITY_MAP)
                .fillna("unknown")
            )

        # ----------------------------------------------------------
        # Normalize Category
        # ----------------------------------------------------------

        logger.info(
            "Normalizing categories"
        )

        if "category" in df.columns:

            df["category_clean"] = (
                df["category"]
                .astype(str)
                .str.strip()
                .str.lower()
                .map(CATEGORY_MAP)
                .fillna(df["category"])
            )

        # ----------------------------------------------------------
        # Clean Cost
        # ----------------------------------------------------------

        logger.info(
            "Cleaning cost column"
        )

        if "cost" in df.columns:

            df["cost_clean"] = (
                df["cost"]
                .apply(clean_cost)
            )

            df["cost_clean"] = (
                pd.to_numeric(
                    df["cost_clean"],
                    errors="coerce"
                )
            )

        # ----------------------------------------------------------
        # Generate Quality Flags
        # ----------------------------------------------------------

        logger.info(
            "Generating quality flags"
        )

        df["quality_flags"] = (
            df.apply(
                create_quality_flags,
                axis=1
            )
        )

        # ----------------------------------------------------------
        # Deduplication
        # ----------------------------------------------------------

        logger.info(
            f"Deduplicating {len(df):,} rows using ticket_id"
        )

        before_dedup = len(df)

        if "ticket_id" in df.columns:

            df = (
                df.sort_values(
                    "ingested_at"
                )
                .drop_duplicates(
                    subset=["ticket_id"],
                    keep="last"
                )
            )

        after_dedup = len(df)

        duplicates_removed = (
            before_dedup - after_dedup
        )

        logger.info(
            f"Removed {duplicates_removed:,} duplicate rows"
        )

        # ----------------------------------------------------------
        # Quality Metrics
        # ----------------------------------------------------------

        flagged_rows = (
            df["quality_flags"]
            .apply(len)
            .gt(0)
            .sum()
        )

        logger.info(
            f"Rows with quality issues: {flagged_rows:,}"
        )

        logger.info(
            "Column null summary:"
        )

        for col in [
            "ticket_id",
            "created_at",
            "resolved_at",
            "priority_clean",
            "category_clean",
            "cost_clean"
        ]:

            if col in df.columns:

                null_count = (
                    df[col]
                    .isna()
                    .sum()
                )

                logger.info(
                    f"{col}: {null_count:,} nulls"
                )

        logger.info(
            f"Final Silver row count: {len(df):,}"
        )

        # ----------------------------------------------------------
        # Write Silver
        # ----------------------------------------------------------

        logger.info(
            "Writing to silver.tickets"
        )

        df.to_sql(
            "tickets",
            engine,
            schema="silver",
            if_exists="replace",
            index=False,
            method="multi",
            chunksize=1000
        )

        logger.info(
            f"Successfully wrote {len(df):,} rows"
        )

        logger.info(
            f"""
Silver Layer Build Completed

Batch ID: {latest_batch_id}
Input Rows: {initial_rows:,}
Output Rows: {len(df):,}
Duplicates Removed: {duplicates_removed:,}
Quality Issues: {flagged_rows:,}
"""
        )

    except Exception as e:

        logger.exception(
            f"Silver Layer Failed: {str(e)}"
        )

        raise


# ------------------------------------------------------------------
# Entry Point
# ------------------------------------------------------------------

if __name__ == "__main__":
    build_silver()