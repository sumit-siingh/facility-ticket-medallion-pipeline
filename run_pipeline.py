import json
import pandas as pd

from sqlalchemy import text
from pprint import pprint

from utils.db import get_engine
from utils.db_init import init_schemas
from utils.pretty import print_data_profile,print_gold_design

from pipeline.bronze import load_bronze
from pipeline.silver import build_silver
from pipeline.gold import build_gold

from agents.data_quality_agent import DataQualitySchemaAgent
from agents.gold_design_agent import GoldDesignAgent


engine = get_engine()

def main():

    # --------------------------------------------------
    # STEP 1: Initialize Schemas
    # --------------------------------------------------

    print("Initializing schemas...")
    init_schemas()

    # --------------------------------------------------
    # STEP 2: Run pipeline
    # --------------------------------------------------
    print("Running Bronze...")
    load_bronze()

    print("Running Silver...")
    build_silver()

    # --------------------------------------------------
    # STEP 3: Load Silver data (FINAL CLEAN DATA)
    # --------------------------------------------------
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT * FROM silver.tickets"), conn)

    # --------------------------------------------------
    # STEP 4: Rule-based agent (profiling)
    # --------------------------------------------------
    dq_agent = DataQualitySchemaAgent()

    profile = dq_agent.profile(df)
    schema = dq_agent.infer_schema(df)

    print("\n=== DATA PROFILE ===")
    print_data_profile(profile)

    # --------------------------------------------------
    # STEP 5: LLM-based Gold Design Agent
    # --------------------------------------------------
    gold_agent = GoldDesignAgent()

    result = gold_agent.run(schema, profile)

    with open("outputs/gold_recommendations.txt", "w") as f:
        f.write(result["raw_llm_output"])

    print("\n=== GOLD DESIGN OUTPUT ===")
    print_gold_design(result)
    # --------------------------------------------------
    # STEP 6: Run Gold Pipeline
    # --------------------------------------------------

    print("\nRunning Gold...")
    build_gold()

    print("\n=== IMPLEMENTED GOLD TABLES ===")
    print("- gold.ticket_kpis")
    print("- gold.building_hotspots")
    print("- gold.assignee_performance")


if __name__ == "__main__":
    main()