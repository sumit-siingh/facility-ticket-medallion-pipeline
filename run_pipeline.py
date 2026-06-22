# from pipeline.bronze import load_bronze
# from pipeline.silver import build_silver
# from pipeline.gold import build_gold

# from utils.db_init import init_schemas

# def main():
#     print("Initializing schemas...")
#     init_schemas()

#     print("Running Bronze layer...")
#     load_bronze()

#     print("Running Silver layer...")
#     build_silver()

#     print("Running Gold layer...")
#     build_gold()

# if __name__ == "__main__":
#     main()


from sqlalchemy import text
import pandas as pd

from utils.db import get_engine

from pipeline.bronze import load_bronze
from pipeline.silver import build_silver
from pipeline.gold import build_gold

from agents.data_quality_agent import DataQualitySchemaAgent
from agents.gold_design_agent import GoldDesignAgent


engine = get_engine()


def main():

    # --------------------------------------------------
    # STEP 1: Run pipeline
    # --------------------------------------------------
    print("Running Bronze...")
    load_bronze()

    print("Running Silver...")
    build_silver()

    # --------------------------------------------------
    # STEP 2: Load Silver data (FINAL CLEAN DATA)
    # --------------------------------------------------
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT * FROM silver.tickets"), conn)

    # --------------------------------------------------
    # STEP 3: Rule-based agent (profiling)
    # --------------------------------------------------
    dq_agent = DataQualitySchemaAgent()

    profile = dq_agent.profile(df)
    schema = dq_agent.infer_schema(df)

    print("\n=== DATA PROFILE ===")
    print(profile)

    # --------------------------------------------------
    # STEP 4: LLM-based Gold Design Agent
    # --------------------------------------------------
    gold_agent = GoldDesignAgent()

    result = gold_agent.run(schema, profile)

    with open("outputs/gold_recommendations.txt", "w") as f:
        f.write(result["raw_llm_output"])

    print("\n=== GOLD DESIGN OUTPUT ===")
    print(result)

    # --------------------------------------------------
    # STEP 5: Run Gold Pipeline
    # --------------------------------------------------

    print("\nRunning Gold...")
    build_gold()

    print("\n=== IMPLEMENTED GOLD TABLES ===")
    print("- gold.ticket_kpis")
    print("- gold.building_hotspots")
    print("- gold.assignee_performance")


if __name__ == "__main__":
    main()