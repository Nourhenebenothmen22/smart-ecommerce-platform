import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://postgres:postgres@localhost:5433/ecommerce_ml_db")
with engine.connect() as conn:
    tables = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")).fetchall()
    print("Tables:", [t[0] for t in tables])
    for table in [t[0] for t in tables]:
        cols = conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}'")).fetchall()
        print(f"Columns in {table}:", [c[0] for c in cols])
