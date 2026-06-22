from sqlalchemy import text
from utils.db import get_engine

def init_schemas():
    engine = get_engine()

    with open("sql/schemas.sql", "r") as f:
        statements = f.read().split(";")

    with engine.begin() as conn:
        for stmt in statements:
            stmt = stmt.strip()
            if stmt:
                conn.execute(text(stmt))