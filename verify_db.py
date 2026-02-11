import pandas as pd
from sqlalchemy import create_engine, text
from config import DATABASE_URL

def verify():
    print(f"Connecting to {DATABASE_URL}")
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check table existence
        tables = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';")).fetchall()
        print("Tables:", [t[0] for t in tables])
        
        # Check indicators count
        try:
            count = conn.execute(text("SELECT count(*) FROM indicators")).scalar()
            print(f"Total Indicators: {count}")
            
            # Check by source
            summary = pd.read_sql("SELECT source, indicator_key, count(*) as n FROM indicators GROUP BY 1, 2", conn)
            print("\nSummary by Source/Indicator:")
            print(summary)
        except Exception as e:
            print(f"Error querying indicators: {e}")

if __name__ == "__main__":
    verify()
