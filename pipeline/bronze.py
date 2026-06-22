# pipeline/bronze.py

import hashlib
import json
import logging
import uuid

from datetime import datetime, timezone

import pandas as pd
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
# Config
# ------------------------------------------------------------------

SOURCE_FILE = "data/raw_tickets.csv"

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def get_file_hash(file_path: str) -> str:
    """
    Hash entire file to detect duplicate ingestion.
    """
    with open(file_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def generate_row_hash(row):
    """
    Deterministic hash used for:
    - lineage
    - deduplication
    - replay detection
    """

    payload = json.dumps(
        row.to_dict(),
        sort_keys=True,
        default=str
    )

    return hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()


def table_exists():
    """
    Check whether bronze table already exists.
    """

    query = """
    SELECT EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'bronze'
        AND table_name = 'tickets_raw'
    );
    """

    with engine.connect() as conn:
        return conn.execute(text(query)).scalar()


def is_file_already_loaded(file_hash: str) -> bool:
    """
    Prevent duplicate ingestion of same file.
    """

    query = """
    SELECT 1
    FROM bronze.tickets_raw
    WHERE source_file_hash = :file_hash
    LIMIT 1
    """

    with engine.connect() as conn:
        result = conn.execute(
            text(query),
            {"file_hash": file_hash}
        ).fetchone()

    return result is not None

def ensure_column_exists():

    if not table_exists():
        return

    query = """
    ALTER TABLE bronze.tickets_raw
    ADD COLUMN IF NOT EXISTS source_file_hash TEXT;
    """

    with engine.begin() as conn:
        conn.execute(text(query))

# ------------------------------------------------------------------
# Bronze Load
# ------------------------------------------------------------------

def load_bronze():

    logger.info("Starting Bronze Layer Ingestion")

    batch_id = str(uuid.uuid4())
    
    try:

        # ----------------------------------------------------------
        # File Hash Check (IDEMPOTENCY)
        # ----------------------------------------------------------

        file_hash = get_file_hash(SOURCE_FILE)

        if table_exists() and is_file_already_loaded(file_hash):
            logger.info("File already ingested. Skipping Bronze load.")
            return {
                "status": "skipped",
                "reason": "file_already_loaded",
                "file_hash": file_hash
            }

        # ----------------------------------------------------------
        # Read Raw File
        # ----------------------------------------------------------

        logger.info(f"Reading source file: {SOURCE_FILE}")

        df = pd.read_csv(
            SOURCE_FILE,
            dtype=str
        )

        logger.info(f"Loaded {len(df):,} rows")
        logger.info(f"Detected {len(df.columns)} columns")

        # ----------------------------------------------------------
        # Add Metadata
        # ----------------------------------------------------------

        ingest_time = datetime.now(timezone.utc)

        logger.info("Adding lineage metadata")

        df["source_file"] = SOURCE_FILE
        df["source_file_hash"] = file_hash
        df["batch_id"] = batch_id
        df["ingested_at"] = ingest_time

        # ----------------------------------------------------------
        # Generate Row Hash
        # ----------------------------------------------------------

        logger.info("Generating row hashes")

        df["row_hash"] = df.apply(generate_row_hash, axis=1)

        duplicate_hashes = df["row_hash"].duplicated().sum()

        logger.info(f"Duplicate hashes in source file: {duplicate_hashes:,}")

        # ----------------------------------------------------------
        # Bronze Metrics
        # ----------------------------------------------------------

        total_nulls = int(df.isna().sum().sum())

        logger.info(f"Total null values: {total_nulls:,}")
        logger.info(f"Batch ID: {batch_id}")

        # ----------------------------------------------------------
        # Ensure schema exists BEFORE writing
        # ----------------------------------------------------------

        if table_exists():
            ensure_column_exists()

        # ----------------------------------------------------------
        # Write Bronze
        # ----------------------------------------------------------

        write_mode = "append" if table_exists() else "replace"

        logger.info(f"Writing to bronze.tickets_raw ({write_mode})")

        df.to_sql(
            "tickets_raw",
            engine,
            schema="bronze",
            if_exists=write_mode,
            index=False,
            method="multi",
            chunksize=1000
        )

        logger.info(f"Successfully loaded {len(df):,} rows")

        # ----------------------------------------------------------
        # Current Bronze Stats
        # ----------------------------------------------------------

        total_rows_query = """
        SELECT COUNT(*)
        FROM bronze.tickets_raw
        """

        with engine.connect() as conn:
            total_rows = conn.execute(text(total_rows_query)).scalar()

        logger.info(f"Bronze table row count: {total_rows:,}")
        logger.info(f"Bronze ingestion completed successfully for batch {batch_id}")

        return {
            "batch_id": batch_id,
            "file_hash": file_hash,
            "rows_loaded": len(df),
            "duplicate_hashes": int(duplicate_hashes),
            "bronze_total_rows": int(total_rows)
        }

    except FileNotFoundError:
        logger.exception(f"Source file not found: {SOURCE_FILE}")
        raise

    except Exception as e:
        logger.exception(f"Bronze ingestion failed: {str(e)}")
        raise


# ------------------------------------------------------------------
# Latest Batch Helper
# ------------------------------------------------------------------

def get_latest_batch_id():

    query = """
    SELECT batch_id
    FROM bronze.tickets_raw
    ORDER BY ingested_at DESC
    LIMIT 1
    """

    with engine.connect() as conn:
        return conn.execute(text(query)).scalar()


# ------------------------------------------------------------------
# Entry Point
# ------------------------------------------------------------------

if __name__ == "__main__":

    summary = load_bronze()

    logger.info(f"Bronze Summary: {summary}")