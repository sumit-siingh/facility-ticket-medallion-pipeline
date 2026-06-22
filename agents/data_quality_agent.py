import pandas as pd


class DataQualitySchemaAgent:
    """
    Deterministic profiling agent.
    NO LLM used here.
    """

    def profile(self, df: pd.DataFrame):

        return {
            "row_count": len(df),
            "columns": list(df.columns),
            "null_rates": df.isna().mean().to_dict(),
            "unique_counts": df.nunique().to_dict(),
        }

    def infer_schema(self, df: pd.DataFrame):

        schema = {}

        for col in df.columns:

            series = df[col].astype(str) 

            numeric_ratio = series.str.replace(".", "", regex=False)\
                                .str.isnumeric()\
                                .fillna(False)\
                                .mean()

            if numeric_ratio > 0.8:
                schema[col] = "INTEGER"

            elif "date" in col.lower() or "time" in col.lower():
                schema[col] = "TIMESTAMP"

            else:
                schema[col] = "TEXT"

        return schema