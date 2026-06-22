from sqlalchemy import create_engine

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/tickets"

def get_engine():
    return create_engine(DATABASE_URL)